import api from './api'

// Chat API
export const chatApi = {
  sendMessage: async (data: {
    agent_id: string
    conversation_id?: string
    message: string
    stream?: boolean
    relevance_threshold?: number
    max_memories?: number
  }) => {
    const response = await api.post('/api/v1/chat/message', data)
    return response.data
  },

  getHistory: async (conversationId: string, limit?: number) => {
    const params = limit ? { limit } : {}
    const response = await api.get(`/api/v1/chat/conversations/${conversationId}/history`, { params })
    return response.data
  },

  getSummary: async (conversationId: string) => {
    const response = await api.post(`/api/v1/chat/conversations/${conversationId}/summary`)
    return response.data
  },
}

