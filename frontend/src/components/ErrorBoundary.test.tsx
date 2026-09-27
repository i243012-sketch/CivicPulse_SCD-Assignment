import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';
import { vi } from 'vitest';

const ThrowError = () => {
  throw new Error('Test Error');
};

describe('ErrorBoundary', () => {
  it('catches error and renders fallback UI', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    consoleError.mockRestore();
  });
});
