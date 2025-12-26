import api from './api'

// Conversation Context API
export const conversationApi = {
  getContext: async (conversationId: string, params?: {
    context_level?: 'minimal' | 'full' | 'detailed'
    agent_id?: string
    filter_date_from?: string
    filter_date_to?: string
    filter_types?: string
    min_relevance?: number
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.context_level) queryParams.append('context_level', params.context_level)
    if (params?.agent_id) queryParams.append('agent_id', params.agent_id)
    if (params?.filter_date_from) queryParams.append('filter_date_from', params.filter_date_from)
    if (params?.filter_date_to) queryParams.append('filter_date_to', params.filter_date_to)
    if (params?.filter_types) queryParams.append('filter_types', params.filter_types)
    if (params?.min_relevance !== undefined) queryParams.append('min_relevance', params.min_relevance.toString())

    const response = await api.get(
      `/api/v1/conversations/${conversationId}/context?${queryParams.toString()}`
    )
    return response.data
  },

  getSummary: async (conversationId: string, style?: 'standard' | 'executive' | 'detailed' | 'brief') => {
    const queryParams = new URLSearchParams()
    if (style) queryParams.append('style', style)

    const response = await api.post(
      `/api/v1/conversations/${conversationId}/summary?${queryParams.toString()}`
    )
    return response.data
  },

  exportContext: async (
    conversationId: string,
    format: 'json' | 'markdown' | 'html',
    options?: {
      context_level?: string
      include_messages?: boolean
      include_memories?: boolean
      include_relationships?: boolean
    }
  ) => {
    const queryParams = new URLSearchParams()
    queryParams.append('format', format)
    if (options?.context_level) queryParams.append('context_level', options.context_level)
    if (options?.include_messages !== undefined) queryParams.append('include_messages', options.include_messages.toString())
    if (options?.include_memories !== undefined) queryParams.append('include_memories', options.include_memories.toString())
    if (options?.include_relationships !== undefined) queryParams.append('include_relationships', options.include_relationships.toString())

    const response = await api.get(
      `/api/v1/conversations/${conversationId}/export?${queryParams.toString()}`,
      { responseType: 'blob' }
    )
    return response.data
  },
}

