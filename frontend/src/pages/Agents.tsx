import { useState, useEffect } from 'react'
import { agentsApi } from '../services/api'
import AgentForm from '../components/Agents/AgentForm'
import AgentInitialization from '../components/Agents/AgentInitialization'

interface Agent {
  agent_id: string
  name: string
  status: string
  created_at: string
  version?: string
  description?: string
}

const Agents = () => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [showInitialization, setShowInitialization] = useState(false)
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')

  useEffect(() => {
    loadAgents()
  }, [statusFilter])

  const loadAgents = async () => {
    try {
      setLoading(true)
      const params: any = { limit: 100 }
      if (statusFilter) params.status = statusFilter
      const response = await agentsApi.getAll(params)
      setAgents(response.agents || [])
    } catch (error: any) {
      console.error('Failed to load agents:', error)
      // Set empty array on error to prevent blank screen
      setAgents([])
      const errorMsg = error?.response?.data?.detail || error?.message || 'Failed to load agents'
      alert(`Failed to load agents: ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  const activateAgent = async (agentId: string) => {
    try {
      await agentsApi.updateStatus(agentId, 'active')
      await loadAgents()
    } catch (error: any) {
      console.error('Failed to activate agent:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to activate agent'
      alert(`Failed to activate agent: ${errorMessage}`)
    }
  }

  const deactivateAgent = async (agentId: string) => {
    try {
      await agentsApi.updateStatus(agentId, 'inactive')
      await loadAgents()
    } catch (error: any) {
      console.error('Failed to deactivate agent:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to deactivate agent'
      alert(`Failed to deactivate agent: ${errorMessage}`)
    }
  }

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-2 py-1 rounded text-xs font-medium'
    switch (status) {
      case 'active':
        return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`
      case 'inactive':
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200`
      case 'error':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`
      default:
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`
    }
  }

  const filteredAgents = agents.filter((agent) =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.agent_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Agents</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Manage your AI agents</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 transition-colors text-sm font-medium"
        >
          Register Agent
        </button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-4 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="error">Error</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">Loading...</div>
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-12 text-center">
          <p className="text-gray-600 dark:text-gray-400">No agents found</p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-4 text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            Register your first agent
          </button>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Agent
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Version
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAgents.map((agent) => (
                <tr key={agent.agent_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {agent.name}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {agent.agent_id}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={getStatusBadge(agent.status)}>{agent.status}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                    {agent.version || 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                    {new Date(agent.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setSelectedAgentId(agent.agent_id)
                          setShowInitialization(true)
                        }}
                        className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        title="Initialize agent with memories"
                      >
                        Initialize
                      </button>
                      {agent.status === 'active' ? (
                        <button
                          onClick={() => deactivateAgent(agent.agent_id)}
                          className="px-3 py-1 text-xs bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
                        >
                          Deactivate
                        </button>
                      ) : (
                        <button
                          onClick={() => activateAgent(agent.agent_id)}
                          className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                        >
                          Activate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <AgentForm
          onClose={async () => {
            setShowForm(false)
            // Small delay to ensure form closes before reloading
            await new Promise(resolve => setTimeout(resolve, 100))
            await loadAgents()
          }}
          onSuccess={async () => {
            // Don't close form here, let the button handler do it
            // Just reload agents
            await loadAgents()
          }}
        />
      )}

      {showInitialization && selectedAgentId && (
        <AgentInitialization
          agentId={selectedAgentId}
          onClose={() => {
            setShowInitialization(false)
            setSelectedAgentId(null)
          }}
        />
      )}
    </div>
  )
}

export default Agents
