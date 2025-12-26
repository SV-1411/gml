# State Management

## State Management Architecture

The dashboard uses a multi-layered state management approach:

1. **Global State** - Zustand
2. **Server State** - TanStack Query
3. **Form State** - React Hook Form
4. **Local State** - React useState/useReducer

## Global State (Zustand)

### Store Structure (`src/store/useStore.ts`)

```typescript
interface Store {
  // User State
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;
  
  // UI State
  sidebarOpen: boolean;
  darkMode: boolean;
  notifications: Notification[];
  
  // Filter State
  dateRange: { from: string; to: string };
  selectedAgents: string[];
  selectedStatus: string[];
  
  // Cache State
  lastUpdate: number;
  cacheInvalidated: boolean;
}
```

### Usage
```typescript
// Get state
const user = useStore((state) => state.user);

// Update state
const setUser = useStore((state) => state.setUser);
setUser(newUser);

// Helper hooks
const { showSuccess, showError } = useNotification();
```

## Server State (TanStack Query)

### Query Hooks

#### useAgents
```typescript
const { agents, loading, error, refetch } = useAgents({
  skip: 0,
  limit: 10,
  status: 'active'
});
```

#### useCosts
```typescript
const { costs, loading, error } = useCosts({
  start_date: '2024-01-01',
  end_date: '2024-12-31'
});
```

#### useMetrics
```typescript
const { metrics, loading, error } = useMetrics();
```

### Mutation Hooks

#### useCreateAgent
```typescript
const createAgent = useCreateAgent();

createAgent.mutate({
  name: 'Agent Name',
  description: 'Description',
  framework: 'CrewAI'
}, {
  onSuccess: (data) => {
    showSuccess('Agent created');
  },
  onError: (error) => {
    showError('Failed to create agent');
  }
});
```

### Query Configuration

- **Stale Time**: How long data is considered fresh
- **Cache Time**: How long data stays in cache
- **Refetch Interval**: Background refetch frequency
- **Retry**: Number of retry attempts

## Form State (React Hook Form)

### Form Setup
```typescript
const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema),
  defaultValues: initialData
});
```

### Validation
- **Zod** - Schema validation
- **Inline errors** - Display errors below fields
- **Async validation** - Server-side validation

## Local State (React)

### useState
For component-specific state:
```typescript
const [isOpen, setIsOpen] = useState(false);
const [selectedItem, setSelectedItem] = useState(null);
```

### useReducer
For complex state logic:
```typescript
const [state, dispatch] = useReducer(reducer, initialState);
```

## State Flow Patterns

### Data Fetching Flow
```
Component → Hook → API Service → Backend
                ↓
         React Query Cache
                ↓
         Component Re-render
```

### Mutation Flow
```
User Action → Mutation Hook → API Service → Backend
                                    ↓
                            Success/Error
                                    ↓
                            Query Invalidation
                                    ↓
                            Cache Update
                                    ↓
                            Component Re-render
```

### Real-time Updates Flow
```
WebSocket Event → WebSocket Service → Event Handler
                                        ↓
                                Real-time Hook
                                        ↓
                                State Update
                                        ↓
                                Component Re-render
```

## State Persistence

### LocalStorage
- User token
- UI preferences (dark mode, sidebar state)
- Filter state (optional)

### SessionStorage
- Temporary data
- Form drafts (optional)

## State Synchronization

### Cache Invalidation
```typescript
// Invalidate specific query
queryClient.invalidateQueries({ queryKey: ['agents'] });

// Invalidate all queries
queryClient.invalidateQueries();
```

### Optimistic Updates
```typescript
queryClient.setQueryData(['agent', id], newData);
```

## Best Practices

### 1. Use Appropriate State Type
- **Global State**: Shared across components
- **Server State**: Data from API
- **Form State**: Form inputs
- **Local State**: Component-specific

### 2. Minimize Global State
- Only store truly global data
- Use server state for API data
- Use local state for UI state

### 3. Cache Strategy
- Set appropriate stale times
- Use background refetching
- Invalidate on mutations

### 4. Error Handling
- Handle errors at hook level
- Show user-friendly messages
- Log errors for debugging

---

**Last Updated**: $(date)

