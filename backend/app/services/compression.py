"""Lossless entropy compression for expert weights (rANS)."""
import struct
import os
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path


# rANS constants
RANS_PRECISION = 16
RANS_MAX_FREQ = 1 << RANS_PRECISION
RANS_SCALE = 1 << RANS_PRECISION


@dataclass
class RANSTable:
    """Static rANS encoding/decoding table."""
    cum_freq: List[int]  # Cumulative frequencies for 256 symbols
    freq: List[int]      # Frequencies for 256 symbols
    norm: int            # Normalization factor


def build_static_table(data: bytes) -> RANSTable:
    """Build a static rANS table from data frequencies."""
    freq = [0] * 256
    for b in data:
        freq[b] += 1

    # Ensure no zero frequencies (add 1 for unseen symbols)
    for i in range(256):
        if freq[i] == 0:
            freq[i] = 1

    # Scale to RANS_MAX_FREQ
    total = sum(freq)
    scale = RANS_MAX_FREQ / total
    scaled_freq = [max(1, int(f * scale)) for f in freq]

    # Adjust to sum exactly to RANS_MAX_FREQ
    diff = RANS_MAX_FREQ - sum(scaled_freq)
    if diff > 0:
        # Add to most frequent symbols
        for i in sorted(range(256), key=lambda x: freq[x], reverse=True):
            if diff <= 0:
                break
            add = min(diff, RANS_MAX_FREQ - scaled_freq[i])
            scaled_freq[i] += add
            diff -= add

    # Build cumulative frequencies
    cum_freq = [0] * 257
    for i in range(256):
        cum_freq[i + 1] = cum_freq[i] + scaled_freq[i]

    return RANSTable(cum_freq=cum_freq, freq=scaled_freq, norm=RANS_MAX_FREQ)


def rans_encode(data: bytes, table: RANSTable) -> bytes:
    """Encode data using rANS with given table."""
    state = RANS_SCALE
    output = []

    # Process backwards for stack-like encoding
    for b in reversed(data):
        freq = table.freq[b]
        cum = table.cum_freq[b]
        state = ((state // freq) << RANS_PRECISION) + (state % freq) + cum

    # Flush state
    while state >= RANS_SCALE:
        output.append(state & 0xFF)
        state >>= 8

    output.append(state & 0xFF)
    return bytes(reversed(output))


def rans_decode(encoded: bytes, table: RANSTable, original_len: int) -> bytes:
    """Decode rANS encoded data."""
    # Load initial state
    state = 0
    pos = 0
    for _ in range(8):
        if pos < len(encoded):
            state = (state << 8) | encoded[pos]
            pos += 1

    output = bytearray()

    for _ in range(original_len):
        slot = state & (RANS_MAX_FREQ - 1)
        # Binary search for symbol
        lo, hi = 0, 256
        while lo < hi:
            mid = (lo + hi) // 2
            if table.cum_freq[mid] <= slot:
                lo = mid + 1
            else:
                hi = mid
        symbol = lo - 1
        output.append(symbol)

        freq = table.freq[symbol]
        cum = table.cum_freq[symbol]
        state = freq * (state >> RANS_PRECISION) + slot - cum

        # Renormalize
        while state < RANS_SCALE and pos < len(encoded):
            state = (state << 8) | encoded[pos]
            pos += 1

    return bytes(output)


@dataclass
class CompressedBlock:
    """Compressed expert block with metadata."""
    layer: int
    expert_id: int
    original_size: int
    compressed_data: bytes
    checksum: int  # CRC32 of original data


@dataclass
class CompressionIndex:
    """Index for compressed container."""
    version: int = 1
    table: Optional[RANSTable] = None
    blocks: Dict[Tuple[int, int], CompressedBlock] = None

    def __post_init__(self):
        if self.blocks is None:
            self.blocks = {}


class ExpertCompressor:
    """Compressor for MoE expert weights."""

    def __init__(self, container_path: str):
        self._container_path = Path(container_path)
        self._table: Optional[RANSTable] = None
        self._index = CompressionIndex()

    def prepare(self, sample_data: bytes = None) -> RANSTable:
        """Build static table from sample data or full scan."""
        if sample_data:
            self._table = build_static_table(sample_data)
        else:
            # Scan all expert files to build table
            all_data = bytearray()
            for exp_file in self._container_path.glob("layer_*_expert_*.bin"):
                all_data.extend(exp_file.read_bytes())
            self._table = build_static_table(bytes(all_data))
        self._index.table = self._table
        return self._table

    def compress_expert(self, layer: int, expert_id: int, data: bytes) -> CompressedBlock:
        """Compress a single expert."""
        if self._table is None:
            raise RuntimeError("Table not prepared. Call prepare() first.")

        import zlib
        checksum = zlib.crc32(data) & 0xFFFFFFFF
        compressed = rans_encode(data, self._table)

        block = CompressedBlock(
            layer=layer,
            expert_id=expert_id,
            original_size=len(data),
            compressed_data=compressed,
            checksum=checksum,
        )
        self._index.blocks[(layer, expert_id)] = block
        return block

    def decompress_expert(self, layer: int, expert_id: int) -> bytes:
        """Decompress a single expert."""
        block = self._index.blocks.get((layer, expert_id))
        if block is None:
            raise KeyError(f"Expert (layer={layer}, expert_id={expert_id}) not in index")

        decompressed = rans_decode(block.compressed_data, self._table, block.original_size)

        import zlib
        if (zlib.crc32(decompressed) & 0xFFFFFFFF) != block.checksum:
            raise ValueError(f"Checksum mismatch for expert (layer={layer}, expert_id={expert_id})")

        return decompressed

    def save_index(self, index_path: Path):
        """Save compression index to disk."""
        import json
        data = {
            "version": self._index.version,
            "cum_freq": self._index.table.cum_freq if self._index.table else [],
            "freq": self._index.table.freq if self._index.table else [],
            "blocks": {
                f"{layer},{expert_id}": {
                    "original_size": block.original_size,
                    "compressed_size": len(block.compressed_data),
                    "checksum": block.checksum,
                }
                for (layer, expert_id), block in self._index.blocks.items()
            }
        }
        index_path.write_text(json.dumps(data))

    def load_index(self, index_path: Path):
        """Load compression index from disk."""
        import json
        data = json.loads(index_path.read_text())
        self._index.version = data["version"]
        self._table = RANSTable(
            cum_freq=data["cum_freq"],
            freq=data["freq"],
            norm=RANS_MAX_FREQ,
        )
        self._index.table = self._table

        # Load compressed blocks from sidecar files
        for key_str, block_data in data["blocks"].items():
            layer, expert_id = map(int, key_str.split(","))
            cz_file = self._container_path / f"layer_{layer}_expert_{expert_id}.bin.cz"
            if cz_file.exists():
                compressed_data = cz_file.read_bytes()
                block = CompressedBlock(
                    layer=layer,
                    expert_id=expert_id,
                    original_size=block_data["original_size"],
                    compressed_data=compressed_data,
                    checksum=block_data["checksum"],
                )
                self._index.blocks[(layer, expert_id)] = block


def compress_container(container_path: str, output_path: str, sample_data: bytes = None) -> Dict:
    """One-time compression pass for a model container."""
    compressor = ExpertCompressor(container_path)
    table = compressor.prepare(sample_data)

    stats = {
        "total_original": 0,
        "total_compressed": 0,
        "blocks": 0,
    }

    os.makedirs(output_path, exist_ok=True)

    for exp_file in Path(container_path).glob("layer_*_expert_*.bin"):
        # Parse layer and expert_id from filename
        name = exp_file.stem  # e.g., "layer_5_expert_3"
        parts = name.split("_")
        layer = int(parts[1])
        expert_id = int(parts[3])

        data = exp_file.read_bytes()
        block = compressor.compress_expert(layer, expert_id, data)

        # Write compressed block
        out_file = Path(output_path) / f"layer_{layer}_expert_{expert_id}.bin.cz"
        out_file.write_bytes(block.compressed_data)

        stats["total_original"] += block.original_size
        stats["total_compressed"] += len(block.compressed_data)
        stats["blocks"] += 1

    # Save index
    compressor.save_index(Path(output_path) / "compression_index.json")

    stats["ratio"] = stats["total_compressed"] / stats["total_original"] if stats["total_original"] > 0 else 0
    return stats


def decompress_expert_data(compressed: bytes, table: RANSTable, original_size: int) -> bytes:
    """Decompress expert data at cache-fill time."""
    return rans_decode(compressed, table, original_size)
