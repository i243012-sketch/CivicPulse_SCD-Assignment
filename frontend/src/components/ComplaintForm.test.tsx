import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ComplaintForm } from './ComplaintForm';
import { api } from '../api/client';
import { vi } from 'vitest';

vi.mock('../api/client', () => ({
  api: {
    createComplaint: vi.fn(),
  },
}));

describe('ComplaintForm', () => {
  it('submits a valid form successfully', async () => {
    (api.createComplaint as any).mockResolvedValueOnce({});
    const onSuccess = vi.fn();
    render(<ComplaintForm onSuccess={onSuccess} />);

    fireEvent.change(screen.getByLabelText(/Complaint Description/i), { target: { value: 'This is a valid long description for testing.' } });
    fireEvent.change(screen.getByLabelText(/Location/i), { target: { value: 'Main Street' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Submit Complaint/i }));

    await waitFor(() => {
      expect(api.createComplaint).toHaveBeenCalledWith({
        text: 'This is a valid long description for testing.',
        location: 'Main Street',
        reporter_contact: undefined,
      });
      expect(onSuccess).toHaveBeenCalled();
    });
  });
});
