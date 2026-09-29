import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from './Dashboard';
import { api } from '../api/client';
import { vi } from 'vitest';

vi.mock('../api/client', () => ({
  api: {
    getStats: vi.fn(),
  },
}));

describe('Dashboard', () => {
  it('renders stats successfully', async () => {
    (api.getStats as any).mockResolvedValue({
      by_category: [{ category: 'roads', count: 5 }],
      by_priority: [{ priority: 'low', count: 5 }],
      total_complaints: 5
    });

    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Complaints')).toBeInTheDocument();
      expect(screen.getByText('roads')).toBeInTheDocument();
      expect(screen.getAllByText('5')).toHaveLength(3); // total + category + priority
    });
  });
});
