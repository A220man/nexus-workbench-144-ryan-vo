import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import axios from 'axios'


// Types
interface Model {
  id: string
  name: string
  size_gb: number
  quantization: string
  backend: string
  path: string
}

interface CachePolicy {
  name: string
  description: string
  enabled: boolean
}

interface CacheStats {
  hit_rate: number
  total_requests: number
  hits: number
  misses: number
  evictions: number
  current_size_mb: number
  max_size_mb: number
}

// API client
const api = axios.create({
  baseURL: '/api',
})

// Components
function Header() {
  const location = useLocation()
  return (
    <header className="header">
      <h1>Nexus Workbench</h1>
      <nav className="nav">
        <Link to="/" className={location.pathname === '/' ? 'active' : ''}>Dashboard</Link>
        <Link to="/models" className={location.pathname === '/models' ? 'active' : ''}>Models</Link>
        <Link to="/chat" className={location.pathname === '/chat' ? 'active' : ''}>Chat</Link>
        <Link to="/cache" className={location.pathname === '/cache' ? 'active' : ''}>Cache</Link>
      </nav>
    </header>
  )
}

function Dashboard() {
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await api.get('/v1/cache/stats')
        setStats(response.data)
      } catch (err) {
        setError('Failed to load cache statistics')
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  if (loading) return <div className="loading"><div className="spinner" /></div>
  if (error) return <div className="error">{error}</div>

  return (
    <div>
      <h1>Dashboard</h1>
      <p style={{ marginBottom: '2rem', color: '#64748b' }}>
        Monitor your MoE model inference performance and cache efficiency.
      </p>
      <div className="grid grid-3">
        <div className="card stat">
          <span className="stat-value">{stats?.hit_rate?.toFixed(1) || 0}%</span>
          <span className="stat-label">Cache Hit Rate</span>
        </div>
        <div className="card stat">
          <span className="stat-value">{(stats?.current_size_mb || 0).toFixed(1)} MB</span>
          <span className="stat-label">Current Cache Size</span>
        </div>
        <div className="card stat">
          <span className="stat-value">{stats?.total_requests || 0}</span>
          <span className="stat-label">Total Requests</span>
        </div>
      </div>
      <div className="card">
        <h2>Recent Activity</h2>
        <div className="empty">No recent activity. Start a chat session to see inference metrics.</div>
      </div>
    </div>
  )
}

function ModelsPage() {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchModels() {
      try {
        const response = await api.get('/v1/models')
        setModels(response.data.models)
      } catch (err) {
        setError('Failed to load models')
      } finally {
        setLoading(false)
      }
    }
    fetchModels()
  }, [])

  if (loading) return <div className="loading"><div className="spinner" /></div>
  if (error) return <div className="error">{error}</div>

  return (
    <div>
      <h1>Models</h1>
      <p style={{ marginBottom: '2rem', color: '#64748b' }}>
        Manage and configure your MoE models for inference.
      </p>
      <div className="grid grid-2">
        {models.map((model) => (
          <div key={model.id} className="card">
            <h2>{model.name}</h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
              <span className="badge badge-info">{model.quantization}</span>
              <span className="badge badge-info">{model.backend}</span>
              <span className="badge badge-info">{model.size_gb} GB</span>
            </div>
            <p style={{ color: '#64748b', fontSize: '0.875rem' }}>
              Path: {model.path}
            </p>
          </div>
        ))}
      </div>
      {models.length === 0 && (
        <div className="card empty">
          No models configured. Add a model to get started.
        </div>
      )}
    </div>
  )
}

function ChatPage() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [model, setModel] = useState('glm-5.3-colibri')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await api.post('/v1/chat/completions', {
        model,
        messages: [...messages, userMessage],
        stream: false,
      })
      const assistantMessage = {
        role: 'assistant',
        content: response.data.choices[0]?.message?.content || 'No response',
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error: Failed to get response' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>Chat</h1>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="input"
          style={{ width: 'auto', maxWidth: '300px' }}
        >
          <option value="glm-5.3-colibri">GLM-5.3 Colibri (int4, CUDA)</option>
        </select>
      </div>
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: '400px' }}>
        <div style={{ flex: 1, overflowY: 'auto', marginBottom: '1rem', maxHeight: '400px' }}>
          {messages.length === 0 ? (
            <div className="empty">Start a conversation with the model.</div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} style={{ marginBottom: '1rem', padding: '0.75rem', background: msg.role === 'user' ? '#dbeafe' : '#f1f5f9', borderRadius: '8px', maxWidth: '80%', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
                <p style={{ marginTop: '0.5rem' }}>{msg.content}</p>
              </div>
            ))
          )}
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="input"
            style={{ flex: 1 }}
            disabled={loading}
          />
          <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}

function CachePage() {
  const [policies, setPolicies] = useState<CachePolicy[]>([])
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [policiesRes, statsRes] = await Promise.all([
          api.get('/v1/cache/policies'),
          api.get('/v1/cache/stats'),
        ])
        setPolicies(policiesRes.data.policies)
        setStats(statsRes.data)
      } catch (err) {
        setError('Failed to load cache data')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handlePolicyToggle = async (policyName: string, enable: boolean) => {
    try {
      await api.post(`/v1/cache/policies/${policyName}/${enable ? 'enable' : 'disable'}`)
      setPolicies((prev) =>
        prev.map((p) =>
          p.name === policyName ? { ...p, enabled: enable } : { ...p, enabled: false }
        )
      )
    } catch (err) {
      alert('Failed to update policy')
    }
  }

  if (loading) return <div className="loading"><div className="spinner" /></div>
  if (error) return <div className="error">{error}</div>

  return (
    <div>
      <h1>Expert Cache</h1>
      <p style={{ marginBottom: '2rem', color: '#64748b' }}>
        Configure expert cache placement policies and monitor performance.
      </p>
      <div className="grid grid-2">
        <div className="card">
          <h2>Placement Policies</h2>
          {policies.map((policy) => (
            <div key={policy.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderBottom: '1px solid #e2e8f0' }}>
              <div>
                <strong>{policy.name}</strong>
                <p style={{ fontSize: '0.875rem', color: '#64748b' }}>{policy.description}</p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className={`badge ${policy.enabled ? 'badge-success' : 'badge-info'}`}>
                  {policy.enabled ? 'Active' : 'Inactive'}
                </span>
                <button
                  className={`btn ${policy.enabled ? 'btn-secondary' : 'btn-primary'}`}
                  onClick={() => handlePolicyToggle(policy.name, !policy.enabled)}
                  disabled={policy.enabled}
                >
                  {policy.enabled ? 'Disable' : 'Enable'}
                </button>
              </div>
            </div>
          ))}
        </div>
        <div className="card">
          <h2>Cache Statistics</h2>
          <div className="grid grid-3" style={{ marginTop: '1rem' }}>
            <div className="stat">
              <span className="stat-value">{stats?.hit_rate?.toFixed(1) || 0}%</span>
              <span className="stat-label">Hit Rate</span>
            </div>
            <div className="stat">
              <span className="stat-value">{stats?.hits || 0}</span>
              <span className="stat-label">Hits</span>
            </div>
            <div className="stat">
              <span className="stat-value">{stats?.misses || 0}</span>
              <span className="stat-label">Misses</span>
            </div>
            <div className="stat">
              <span className="stat-value">{stats?.evictions || 0}</span>
              <span className="stat-label">Evictions</span>
            </div>
            <div className="stat">
              <span className="stat-value">{(stats?.current_size_mb || 0).toFixed(1)} MB</span>
              <span className="stat-label">Current Size</span>
            </div>
            <div className="stat">
              <span className="stat-value">{(stats?.max_size_mb || 0).toFixed(1)} MB</span>
              <span className="stat-label">Max Size</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <div className="app">
      <Header />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/cache" element={<CachePage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
