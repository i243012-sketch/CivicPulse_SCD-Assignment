import { render, screen, waitFor } from '@testing-library/react';
import { RuntimeConfigCheck } from './RuntimeConfigCheck';
import { api } from '../api/client';
import { vi } from 'vitest';

vi.mock('../api/client', () => ({
  api: {
    checkHealth: vi.fn(),
  },
}));

describe('RuntimeConfigCheck', () => {
  it('renders children if backend is healthy', async () => {
    (api.checkHealth as any).mockResolvedValue(true);
    
    render(
      <RuntimeConfigCheck>
        <div data-testid="child">App Content</div>
      </RuntimeConfigCheck>
    );
    
    expect(screen.getByText('Connecting to backend services...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByTestId('child')).toBeInTheDocument();
    });
  });

  it('renders error state if backend is unhealthy', async () => {
    (api.checkHealth as any).mockResolvedValue(false);
    
    render(
      <RuntimeConfigCheck>
        <div data-testid="child">App Content</div>
      </RuntimeConfigCheck>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Service Unavailable')).toBeInTheDocument();
    });
  });
});
