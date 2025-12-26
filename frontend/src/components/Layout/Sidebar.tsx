import { NavLink } from 'react-router-dom'
import { useTheme } from '../../contexts/ThemeContext'
import clsx from 'clsx'

interface SidebarProps {
  isOpen: boolean
  onToggle: () => void
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const menuItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/chat', label: 'Chat' },
    { path: '/conversations', label: 'Conversations' },
    { path: '/agents', label: 'Agents' },
    { path: '/memories', label: 'Memories' },
    { path: '/settings', label: 'Settings' },
  ]

  return (
    <aside
      className={clsx(
        'flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300',
        isOpen ? 'w-64' : 'w-20'
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        {isOpen && (
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            GML Dashboard
          </h1>
        )}
        <button
          onClick={onToggle}
          className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 text-sm"
        >
          {isOpen ? '←' : '→'}
        </button>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-4 py-3 rounded transition-colors text-sm font-medium',
                isActive
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              )
            }
          >
            {isOpen && <span>{item.label}</span>}
            {!isOpen && <span className="text-xs">{item.label.charAt(0)}</span>}
          </NavLink>
        ))}
      </nav>

      {isOpen && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-xs text-gray-500 dark:text-gray-400">
            GML Infrastructure v1.0.0
          </div>
        </div>
      )}
    </aside>
  )
}

export default Sidebar
