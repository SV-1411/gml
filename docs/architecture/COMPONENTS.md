# Component Structure

## Component Organization

Components are organized by functionality and reusability.

## Component Hierarchy

```
App
└── MainLayout
    ├── Sidebar
    ├── Header
    └── Router
        ├── AdminDashboard
        ├── OperationsDashboard
        ├── AnalystDashboard
        └── DeveloperDashboard
```

## Component Categories

### 1. Layout Components (`src/components/Layout/`)

#### MainLayout
- **Purpose**: Root layout wrapper
- **Props**: `role`, `userName`, `organizationName`
- **Features**: Sidebar + Header + Content area

#### Sidebar
- **Purpose**: Navigation sidebar
- **Props**: `role`, `activePath`
- **Features**: Role-based navigation, collapsible

#### Header
- **Purpose**: Top header bar
- **Props**: `role`, `userName`
- **Features**: Logo, notifications, user menu, dark mode toggle

### 2. Dashboard Components (`src/components/Dashboard/`)

#### AdminDashboard
- **Purpose**: Admin overview dashboard
- **Data**: Agents, costs, metrics
- **Features**: Metric cards, charts, agent table

#### OperationsDashboard
- **Purpose**: Operations monitoring
- **Data**: System health, alerts, incidents
- **Features**: Health cards, alerts table, real-time metrics

#### AnalystDashboard
- **Purpose**: Analytics and reporting
- **Data**: Costs, trends, top agents
- **Features**: Charts, export functionality

#### DeveloperDashboard
- **Purpose**: Developer tools
- **Status**: Placeholder (needs implementation)

### 3. Common Components (`src/components/Common/`)

#### Data Display
- **MetricCard** - KPI display with trend
- **DataTable** - Sortable, paginated table
- **StatusBadge** - Status indicator
- **EmptyState** - Empty state display

#### Charts
- **AreaChart** - Area chart (Recharts)
- **BarChart** - Bar chart (Recharts)
- **DonutChart** - Donut/Pie chart (Recharts)
- **LineChart** - Line chart (Recharts)
- **RealtimeLineChart** - Real-time streaming chart

#### Forms & Inputs
- **Input** - Text input field
- **Select** - Dropdown select
- **DateRangePicker** - Date range selector
- **Button** - Button component

#### Feedback
- **LoadingSpinner** - Loading indicator
- **Skeleton** - Skeleton loader
- **SkeletonLoader** - Pre-built skeleton variants
- **ErrorBoundary** - Error boundary component
- **AlertNotification** - Alert toast/banner

#### Overlays
- **Modal** - Modal dialog
- **Tooltip** - Tooltip component
- **Dropdown** - Dropdown menu

#### Layout
- **Card** - Container card
- **Divider** - Horizontal divider
- **PageHeader** - Page title and description

### 4. Form Components (`src/components/Forms/`)

#### AgentForm
- **Purpose**: Create/update agents
- **Fields**: Name, description, status, framework, memory limit
- **Validation**: React Hook Form + Zod

#### FilterForm
- **Purpose**: Advanced filtering
- **Fields**: Date range, status, agent, cost range
- **Features**: Live filtering, reset button

#### Modals
- **Modal** - Base modal component
- **ConfirmModal** - Confirmation dialog
- **FormModal** - Modal with form

## Component Patterns

### Props Interface
All components use TypeScript interfaces for props:

```typescript
interface ComponentProps {
  title: string;
  value: number;
  variant?: 'primary' | 'secondary';
  className?: string;
}
```

### Styling
- CSS Modules or separate CSS files
- BEM methodology for class names
- CSS variables for theming

### Accessibility
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus indicators

## Component Reusability

### High Reusability
- **MetricCard** - Used in all dashboards
- **DataTable** - Used for all data tables
- **Button** - Used throughout the app
- **Modal** - Used for all dialogs

### Medium Reusability
- **Charts** - Used in multiple dashboards
- **Forms** - Used for data entry
- **StatusBadge** - Used in tables

### Low Reusability
- **Dashboard Components** - Page-specific
- **Layout Components** - App-specific

## Component Testing

### Unit Tests
- Component rendering
- Props handling
- User interactions
- State changes

### Integration Tests
- Component interactions
- Data flow
- Error handling

## Component Documentation

Each component should include:
- Purpose and usage
- Props interface
- Examples
- Accessibility notes

---

**Last Updated**: $(date)

