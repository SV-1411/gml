import api from './api'

// Batch Operations API
export const batchApi = {
  create: async (data: {
    memories: Array<{
      conversation_id: string
      content: Record<string, any>
      memory_type: 'episodic' | 'semantic' | 'procedural'
      visibility?: 'all' | 'organization' | 'private'
      tags?: string[]
    }>
    skip_duplicates?: boolean
    validate_all?: boolean
  }) => {
    const response = await api.post('/api/v1/memories/batch/create', data)
    return response.data
  },

  delete: async (data: {
    context_ids: string[]
    soft_delete?: boolean
    cascade?: boolean
  }) => {
    const response = await api.post('/api/v1/memories/batch/delete', data)
    return response.data
  },

  export: async (data: {
    context_ids?: string[]
    format?: 'json' | 'csv'
    include_versions?: boolean
    include_vectors?: boolean
    compress?: boolean
    filters?: Record<string, any>
  }) => {
    const response = await api.post('/api/v1/memories/batch/export', data, {
      responseType: 'blob',
    })
    return response.data
  },

  consolidate: async (data: {
    similarity_threshold?: number
    dry_run?: boolean
    merge_strategy?: 'newest' | 'oldest' | 'longest'
  }) => {
    const response = await api.post('/api/v1/memories/batch/consolidate', data)
    return response.data
  },

  reindex: async (data: {
    context_ids?: string[]
    batch_size?: number
    force?: boolean
  }) => {
    const response = await api.post('/api/v1/memories/batch/reindex', data)
    return response.data
  },
}

