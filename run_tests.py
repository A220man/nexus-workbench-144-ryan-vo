
import subprocess
import sys

# Run backend tests
result = subprocess.run([sys.executable, "-m", "pytest", "backend/tests/", "-v"], 
                       cwd="/var/lib/alan-portfolio/workspaces/ryan/nexus-workbench-144-ryan-vo",
                       capture_output=True, text=True)
print("=== BACKEND TESTS ===")
print(result.stdout)
print(result.stderr)
print(f"Return code: {result.returncode}")

# Run frontend tests
result2 = subprocess.run(["npm", "test"], 
                        cwd="/var/lib/alan-portfolio/workspaces/ryan/nexus-workbench-144-ryan-vo/frontend",
                        capture_output=True, text=True)
print("\n=== FRONTEND TESTS ===")
print(result2.stdout)
print(result2.stderr)
print(f"Return code: {result2.returncode}")
