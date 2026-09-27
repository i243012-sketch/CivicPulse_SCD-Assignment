import { render, screen, waitFor } from '@testing-library/react';
import { ComplaintList } from './ComplaintList';
import { api } from '../api/client';
import { vi } from 'vitest';

vi.mock('../api/client', () => ({
  api: {
    listComplaints: vi.fn(),
  },
}));

describe('ComplaintList', () => {
  it('renders complaints successfully', async () => {
    (api.listComplaints as any).mockResolvedValue({
      items: [
        { id: '1', text: 'Issue 1', location: 'Loc 1', category: 'water', priority: 'high', status: 'open', created_at: new Date().toISOString() }
      ],
      total: 1
    });

    render(<ComplaintList />);
    
    await waitFor(() => {
      expect(screen.getByText('Complaints (1)')).toBeInTheDocument();
      expect(screen.getByText('Issue 1')).toBeInTheDocument();
    });
  });
});
