import api from './api'

// Agent API
export const agentApi = {
  initialize: async (agentId: string, params?: {
    conversation_id?: string
    query?: string
    max_tokens?: number
    strategy?: 'semantic' | 'keyword' | 'hybrid' | 'all'
    format_type?: 'narrative' | 'qa' | 'structured'
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.conversation_id) queryParams.append('conversation_id', params.conversation_id)
    if (params?.query) queryParams.append('query', params.query)
    if (params?.max_tokens) queryParams.append('max_tokens', params.max_tokens.toString())
    if (params?.strategy) queryParams.append('strategy', params.strategy)
    if (params?.format_type) queryParams.append('format_type', params.format_type)

    const response = await api.post(
      `/api/v1/agents/${agentId}/initialize?${queryParams.toString()}`,
      {}
    )
    return response.data
  },
}

