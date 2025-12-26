# Architecture Overview

## System Architecture

The GML Infrastructure Dashboard is built with a modern, scalable architecture using React 18, TypeScript, and a microservices-style backend integration.

## Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing

### State Management
- **Zustand** - Global state management
- **TanStack Query (React Query)** - Server state management
- **React Hook Form** - Form state management

### Data Fetching
- **Axios** - HTTP client
- **Socket.IO Client** - WebSocket client
- **TanStack Query** - Caching and synchronization

### UI Components
- **Recharts** - Chart library
- **Custom Components** - Reusable UI components

## Architecture Layers

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (Components, Pages, Layout)           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Application Layer                │
│  (Hooks, State Management)              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Service Layer                   │
│  (API Client, WebSocket)                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Backend API                      │
│  (GML Infrastructure API)               │
└─────────────────────────────────────────┘
```

## Component Architecture

### Layout Components
- **MainLayout** - Root layout wrapper
- **Sidebar** - Navigation sidebar
- **Header** - Top header bar

### Dashboard Components
- **AdminDashboard** - Admin overview
- **OperationsDashboard** - Operations monitoring
- **AnalystDashboard** - Analytics dashboard
- **DeveloperDashboard** - Developer tools

### Common Components
- **MetricCard** - KPI display
- **DataTable** - Sortable table
- **Charts** - Area, Bar, Donut, Line charts
- **Forms** - AgentForm, FilterForm
- **Modals** - Modal, ConfirmModal, FormModal

## Data Flow

### API Data Flow
```
Component → Hook → API Service → Backend API
                ↓
         React Query Cache
                ↓
         Component Update
```

### WebSocket Data Flow
```
Backend → WebSocket Service → Event Handler
                              ↓
                    Real-time Hook
                              ↓
                    State Update
                              ↓
                    Component Re-render
```

## State Management

### Global State (Zustand)
- User authentication
- UI preferences (sidebar, dark mode)
- Notifications
- Filter state
- Cache state

### Server State (React Query)
- Agents data
- Costs data
- Memory data
- Metrics data
- Dashboard data

### Local State (React)
- Component-specific state
- Form state (React Hook Form)
- UI interactions

## File Structure

```
src/
├── components/          # UI components
│   ├── Layout/        # Layout components
│   ├── Dashboard/     # Dashboard pages
│   ├── Common/        # Reusable components
│   └── Forms/         # Form components
├── hooks/             # Custom React hooks
├── services/          # API and WebSocket services
├── store/             # Zustand store
├── styles/            # CSS files
├── types/             # TypeScript types
└── utils/             # Utility functions
```

## Design Patterns

### Component Patterns
- **Container/Presentational** - Separation of logic and presentation
- **Compound Components** - Related components working together
- **Render Props** - Flexible component composition

### State Patterns
- **Custom Hooks** - Reusable state logic
- **Query Hooks** - Server state management
- **Mutation Hooks** - Data mutations

### Service Patterns
- **API Client** - Centralized HTTP client
- **WebSocket Service** - Real-time communication
- **Error Handling** - Centralized error management

## Performance Optimizations

### Code Splitting
- Lazy loading dashboard pages
- Route-based code splitting
- Dynamic imports

### Caching
- React Query caching
- Stale-while-revalidate pattern
- Background refetching

### Memoization
- React.memo for components
- useMemo for expensive calculations
- useCallback for event handlers

## Security

### Authentication
- JWT token storage
- Token refresh mechanism
- Auto-logout on 401

### API Security
- HTTPS in production
- CORS configuration
- Request/response validation

## Scalability

### Horizontal Scaling
- Stateless frontend
- CDN deployment
- Load balancing ready

### Vertical Scaling
- Code splitting
- Lazy loading
- Optimized bundle size

## Monitoring & Observability

### Error Tracking
- Error boundaries
- Console logging
- User-friendly error messages

### Performance Monitoring
- Request duration tracking
- Query performance
- Component render tracking

---

**Last Updated**: $(date)

