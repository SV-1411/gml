import { useEffect, useState } from 'react'
import { agentsApi, healthApi, memoryApi } from '../services/api'

interface Agent {
  id: string
  name: string
  status: string
  created_at: string
}

interface Memory {
  context_id: string
  content: any
  memory_type?: string
  created_at: string
  created_by: string
  storage_url?: string
}

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalAgents: 0,
    activeAgents: 0,
    inactiveAgents: 0,
    totalMemories: 0,
    memoriesByType: {
      episodic: 0,
      semantic: 0,
      procedural: 0,
    },
    filesInStorage: 0,
    totalStorageSize: 0,
    systemHealth: {
      database: 'unknown',
      redis: 'unknown',
      qdrant: 'unknown',
      minio: 'unknown',
    },
  })
  const [loading, setLoading] = useState(true)
  const [agents, setAgents] = useState<Agent[]>([])
  const [memories, setMemories] = useState<Memory[]>([])
  const [recentMemories, setRecentMemories] = useState<Memory[]>([])

  useEffect(() => {
    loadDashboardData()
    const interval = setInterval(() => {
      loadDashboardData()
    }, 30000)
    return () => clearInterval(interval)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const loadDashboardData = async () => {
    try {
      const isInitialLoad = stats.totalAgents === 0 && stats.totalMemories === 0
      if (isInitialLoad) {
        setLoading(true)
      }

      // Load all agents
      const agentsResponse = await agentsApi.getAll({ limit: 1000 })
      const allAgents: Agent[] = agentsResponse.agents || []
      setAgents(allAgents)

      const activeAgents = allAgents.filter((a: any) => a.status === 'active').length
      const inactiveAgents = allAgents.filter((a: any) => a.status === 'inactive').length

      // Load detailed health
      let systemHealth = {
        database: 'unknown',
        redis: 'unknown',
        qdrant: 'unknown',
        minio: 'unknown',
      }
      try {
        const healthResponse = await healthApi.detailed()
        systemHealth = {
          database: healthResponse.database?.status || 'unknown',
          redis: healthResponse.redis?.status || 'unknown',
          qdrant: healthResponse.qdrant?.status || 'unknown',
          minio: healthResponse.minio?.status || 'unknown',
        }
      } catch (error) {
        console.error('Failed to load health:', error)
      }

      // Load all memories
      let allMemories: Memory[] = []
      let totalMemories = 0
      let filesInStorage = 0
      let totalStorageSize = 0
      const memoriesByType = {
        episodic: 0,
        semantic: 0,
        procedural: 0,
      }

      const agentId = localStorage.getItem('agent_id')
      if (agentId) {
        try {
          const memoryResponse = await memoryApi.search({
            query: 'memory',
            limit: 100, // Maximum allowed by API
          })

          allMemories = (memoryResponse.results || []) as Memory[]
          setMemories(allMemories)
          totalMemories = allMemories.length

          // Calculate stats
          allMemories.forEach((mem: Memory) => {
            // Count by type
            const memType = mem.memory_type || 'semantic'
            if (memType === 'episodic') memoriesByType.episodic++
            else if (memType === 'semantic') memoriesByType.semantic++
            else if (memType === 'procedural') memoriesByType.procedural++

            // Count files
            const storageUrl = mem.content?.storage_url || mem.content?.file_url || mem.storage_url
            const fileSize = mem.content?.file_size || 0

            if (storageUrl) {
              filesInStorage++
              totalStorageSize += fileSize
            }
          })

          // Get recent memories (last 10)
          const sortedMemories = [...allMemories].sort((a, b) => {
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          })
          setRecentMemories(sortedMemories.slice(0, 10))
        } catch (error) {
          console.error('Failed to load memories:', error)
        }
      }

      setStats({
        totalAgents: allAgents.length,
        activeAgents,
        inactiveAgents,
        totalMemories,
        memoriesByType,
        filesInStorage,
        totalStorageSize,
        systemHealth,
      })
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const getHealthColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400'
      case 'unhealthy':
        return 'text-red-600 dark:text-red-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getHealthBgColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
      case 'unhealthy':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      default:
        return 'bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">Real-time overview of GML Infrastructure</p>
        </div>
        <button
          onClick={() => {
            setLoading(true)
            loadDashboardData()
          }}
          disabled={loading}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {loading && stats.totalAgents === 0 && stats.totalMemories === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500 dark:text-gray-400">Loading dashboard...</div>
        </div>
      ) : (
        <>
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Agents</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.totalAgents}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {stats.activeAgents} active • {stats.inactiveAgents} inactive
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Memories</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.totalMemories}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {stats.memoriesByType.semantic} semantic • {stats.memoriesByType.episodic} episodic • {stats.memoriesByType.procedural} procedural
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Files in Storage</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.filesInStorage}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {formatFileSize(stats.totalStorageSize)} total
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">System Health</p>
              <p className={`text-2xl font-bold capitalize ${getHealthColor(
                Object.values(stats.systemHealth).every(s => s === 'healthy') ? 'healthy' : 
                Object.values(stats.systemHealth).some(s => s === 'unhealthy') ? 'unhealthy' : 'unknown'
              )}`}>
                {Object.values(stats.systemHealth).every(s => s === 'healthy') ? 'Healthy' : 
                 Object.values(stats.systemHealth).some(s => s === 'unhealthy') ? 'Issues' : 'Unknown'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {Object.values(stats.systemHealth).filter(s => s === 'healthy').length} of 4 services healthy
              </p>
            </div>
          </div>

          {/* System Health Details */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">System Health Status</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.systemHealth).map(([service, status]) => (
                <div
                  key={service}
                  className={`p-4 rounded-lg border ${getHealthBgColor(status)}`}
                >
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 capitalize">{service}</p>
                  <p className={`text-xl font-semibold capitalize ${getHealthColor(status)}`}>
                    {status}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Agents List */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  All Agents ({agents.length})
                </h2>
                <a
                  href="/agents"
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                >
                  View All →
                </a>
              </div>
              {agents.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {agents.map((agent) => (
                    <div
                      key={agent.id}
                      className="p-3 bg-gray-50 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {agent.name || agent.id}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            ID: {agent.id}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                            Created: {new Date(agent.created_at).toLocaleString()}
                          </p>
                        </div>
                        <span
                          className={`px-2 py-1 text-xs rounded ${
                            agent.status === 'active'
                              ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                              : 'bg-gray-100 dark:bg-gray-600 text-gray-800 dark:text-gray-200'
                          }`}
                        >
                          {agent.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-500 dark:text-gray-400">No agents registered yet.</p>
                  <a
                    href="/agents"
                    className="text-sm text-primary-600 dark:text-primary-400 hover:underline mt-2 inline-block"
                  >
                    Register your first agent →
                  </a>
                </div>
              )}
            </div>

            {/* Recent Memories */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Recent Memories ({memories.length} total)
                </h2>
                <a
                  href="/memories"
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                >
                  View All →
                </a>
              </div>
              {recentMemories.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {recentMemories.map((mem) => {
                    const fileName = mem.content?.text || mem.content?.filename || 'Memory content'
                    const fileSize = mem.content?.file_size ? formatFileSize(mem.content.file_size) : null
                    const storageUrl = mem.content?.storage_url || mem.content?.file_url || mem.storage_url
                    const memType = mem.memory_type || 'semantic'

                    return (
                      <div
                        key={mem.context_id}
                        className="p-3 bg-gray-50 dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {typeof fileName === 'string' && fileName.length > 50 
                                  ? fileName.substring(0, 50) + '...' 
                                  : fileName}
                              </p>
                              <span className="px-1.5 py-0.5 text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded capitalize">
                                {memType}
                              </span>
                            </div>
                            {fileSize && storageUrl && (
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {fileSize} • {mem.content?.file_type || ''}
                              </p>
                            )}
                            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                              {new Date(mem.created_at).toLocaleString()}
                            </p>
                          </div>
                          {storageUrl && (
                            <div className="ml-2 flex gap-1">
                              <a
                                href={storageUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs px-2 py-1 bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200 rounded hover:bg-primary-200 dark:hover:bg-primary-800 transition-colors"
                                title="View file"
                              >
                                View
                              </a>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-500 dark:text-gray-400">No memories created yet.</p>
                  <a
                    href="/memories"
                    className="text-sm text-primary-600 dark:text-primary-400 hover:underline mt-2 inline-block"
                  >
                    Create your first memory →
                  </a>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default Dashboard
