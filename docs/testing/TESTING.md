# Testing Guide

## Unit Tests

Run unit tests with Vitest:

```bash
npm test
```

Run tests in watch mode:

```bash
npm test -- --watch
```

Run tests with UI:

```bash
npm run test:ui
```

Generate coverage report:

```bash
npm run test:coverage
```

## Test Structure

- **Unit Tests**: `src/components/**/__tests__/*.test.tsx`
- **Integration Tests**: `src/components/**/__tests__/*.integration.test.tsx`
- **Service Tests**: `src/services/__tests__/*.test.ts`

## Writing Tests

### Component Test Example

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MyComponent } from '../MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### Form Test Example

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should validate form', async () => {
  const user = userEvent.setup();
  render(<MyForm onSubmit={mockSubmit} />);
  
  await user.type(screen.getByLabelText('Name'), 'Test');
  await user.click(screen.getByRole('button', { name: 'Submit' }));
  
  expect(mockSubmit).toHaveBeenCalled();
});
```

## E2E Tests (Cypress)

Run E2E tests:

```bash
npm run test:e2e
```

Open Cypress UI:

```bash
npm run test:e2e:open
```

E2E tests are located in `cypress/e2e/`.

## Test Coverage Goals

- Unit Tests: >80% coverage
- Integration Tests: Critical user flows
- E2E Tests: Main user journeys

