import axios from 'axios'

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const agentId = localStorage.getItem('agent_id')
    if (agentId) {
      config.headers['X-Agent-ID'] = agentId
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error)
  }
)

// Agents API
export const agentsApi = {
  register: async (data: {
    agent_id: string
    name: string
    version?: string
    description?: string
    capabilities: string[]
  }) => {
    const response = await api.post('/api/v1/agents/register', data)
    return response.data
  },
  getAll: async (params?: { status?: string; skip?: number; limit?: number }) => {
    const response = await api.get('/api/v1/agents', { params })
    return response.data
  },
  getById: async (agentId: string) => {
    const response = await api.get(`/api/v1/agents/${agentId}`)
    return response.data
  },
  updateStatus: async (agentId: string, newStatus: string) => {
    const response = await api.patch(`/api/v1/agents/${agentId}/status`, {
      status: newStatus,
    })
    return response.data
  },
}

// Memory API
export const memoryApi = {
  write: async (data: {
    conversation_id: string
    content: Record<string, any>
    memory_type: 'episodic' | 'semantic' | 'procedural'
    visibility?: 'all' | 'organization' | 'private'
    tags?: string[]
  }) => {
    const response = await api.post('/api/v1/memory/write', data)
    return response.data
  },
  update: async (contextId: string, data: {
    conversation_id?: string
    content: Record<string, any>
    memory_type?: 'episodic' | 'semantic' | 'procedural'
    visibility?: 'all' | 'organization' | 'private'
    tags?: string[]
  }) => {
    const response = await api.patch(`/api/v1/memory/${contextId}`, data)
    return response.data
  },
  getById: async (contextId: string) => {
    const response = await api.get(`/api/v1/memory/${contextId}`)
    return response.data
  },
  search: async (data: {
    query: string
    memory_type?: 'episodic' | 'semantic' | 'procedural'
    conversation_id?: string
    limit?: number
  }) => {
    const response = await api.post('/api/v1/memory/search', data)
    return response.data
  },
}

// Agent API (for initialization)
export { agentApi } from './agentApi'

// Memory Versions API
export const memoryVersionsApi = {
  getHistory: async (contextId: string, params?: { limit?: number; offset?: number }) => {
    const response = await api.get(`/api/v1/memories/${contextId}/versions`, { params })
    return response.data
  },
  getVersion: async (contextId: string, versionNumber: number) => {
    const response = await api.get(`/api/v1/memories/${contextId}/versions/${versionNumber}`)
    return response.data
  },
  revert: async (contextId: string, versionNumber: number, authorId?: string) => {
    const response = await api.post(`/api/v1/memories/${contextId}/versions/revert`, {
      version_number: versionNumber,
      author_id: authorId,
    })
    return response.data
  },
  getDiff: async (contextId: string, version1: number, version2?: number) => {
    const params = new URLSearchParams({ version1: version1.toString() })
    if (version2 !== undefined) params.append('version2', version2.toString())
    const response = await api.get(`/api/v1/memories/${contextId}/versions/diff?${params}`)
    return response.data
  },
}

// Search API (Semantic Search)
export const searchApi = {
  semantic: async (data: {
    query: string
    top_k?: number
    threshold?: number
    memory_type?: 'episodic' | 'semantic' | 'procedural'
    conversation_id?: string
    agent_id?: string
    use_cache?: boolean
  }) => {
    const response = await api.post('/api/v1/search/semantic', data)
    return response.data
  },
  keyword: async (data: {
    query: string
    top_k?: number
    memory_type?: 'episodic' | 'semantic' | 'procedural'
    conversation_id?: string
    agent_id?: string
  }) => {
    const response = await api.post('/api/v1/search/keyword', data)
    return response.data
  },
  hybrid: async (data: {
    query: string
    top_k?: number
    threshold?: number
    semantic_weight?: number
    keyword_weight?: number
    memory_type?: 'episodic' | 'semantic' | 'procedural'
    conversation_id?: string
    agent_id?: string
    use_cache?: boolean
  }) => {
    const response = await api.post('/api/v1/search/hybrid', data)
    return response.data
  },
}

// Ollama API
export const ollamaApi = {
  simpleChat: async (message: string, systemMessage?: string, model?: string) => {
    const params = new URLSearchParams({ message })
    if (systemMessage) params.append('system_message', systemMessage)
    if (model) params.append('model', model)
    const response = await api.post(`/api/v1/ollama/simple?${params.toString()}`)
    return response.data
  },
  chat: async (messages: Array<{ role: string; content: string }>, model?: string, temperature?: number) => {
    const response = await api.post('/api/v1/ollama/chat', {
      messages,
      model,
      temperature,
    })
    return response.data
  },
  health: async () => {
    const response = await api.get('/api/v1/ollama/health')
    return response.data
  },
  models: async () => {
    const response = await api.get('/api/v1/ollama/models')
    return response.data
  },
}

// Health API
export const healthApi = {
  check: async () => {
    const response = await api.get('/health')
    return response.data
  },
  detailed: async () => {
    const response = await api.get('/api/v1/health/detailed')
    return response.data
  },
}

// Storage API
export const storageApi = {
  upload: async (file: File, bucket: string = 'uploads') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('bucket', bucket)
    const response = await api.post('/api/v1/storage/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
  getUrl: async (key: string, bucket: string = 'uploads') => {
    const response = await api.get(`/api/v1/storage/url/${key}`, {
      params: { bucket },
    })
    return response.data
  },
}

export default api

