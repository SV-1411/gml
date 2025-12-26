import { useState, useEffect } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { agentsApi } from '../services/api'

const Settings = () => {
  const { theme, toggleTheme } = useTheme()
  const [agentId, setAgentId] = useState('')
  const [availableAgents, setAvailableAgents] = useState<Array<{ agent_id: string; name: string }>>([])

  useEffect(() => {
    setAgentId(localStorage.getItem('agent_id') || '')
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await agentsApi.getAll({})
      const agents = response.agents || []
      setAvailableAgents(agents.map((a: any) => ({ agent_id: a.agent_id, name: a.name || a.agent_id })))
      
      // Auto-select first active agent if no agent ID is set
      if (!localStorage.getItem('agent_id') && agents.length > 0) {
        const activeAgent = agents.find((a: any) => a.status === 'active') || agents[0]
        if (activeAgent) {
          setAgentId(activeAgent.agent_id)
        }
      }
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const handleSaveAgentId = () => {
    if (agentId.trim()) {
      localStorage.setItem('agent_id', agentId.trim())
      alert('Agent ID saved successfully!')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">Manage your application settings</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Agent ID</h2>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Set your default agent ID for API requests. This will be used in the X-Agent-ID header.
        </p>
        
        {availableAgents.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select from registered agents:
            </label>
            <select
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="">-- Select an agent --</option>
              {availableAgents.map((agent) => (
                <option key={agent.agent_id} value={agent.agent_id}>
                  {agent.name} ({agent.agent_id})
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Or enter agent ID manually:
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              placeholder="Enter agent ID..."
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            />
            <button
              onClick={handleSaveAgentId}
              className="px-4 py-2 bg-primary-600 text-white rounded border border-primary-600 hover:bg-primary-700 transition-colors text-sm font-medium"
              disabled={!agentId.trim()}
            >
              Save
            </button>
          </div>
        </div>

        {!agentId && (
          <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              Warning: No agent ID set. You need to set an agent ID to create memories. 
              Go to the Agents page to register an agent first.
            </p>
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Theme</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Switch between light and dark themes.
        </p>
        <button
          onClick={toggleTheme}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
        >
          {theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
        </button>
      </div>
    </div>
  )
}

export default Settings
