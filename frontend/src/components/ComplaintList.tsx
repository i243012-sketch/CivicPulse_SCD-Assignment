import { useEffect, useState } from 'react';
import { api, Complaint } from '../api/client';

export function ComplaintList() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const loadComplaints = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listComplaints({
        page,
        page_size: 20,
        category: categoryFilter || undefined,
        priority: priorityFilter || undefined,
        status: statusFilter || undefined,
      });
      setComplaints(response.items);
      setTotal(response.total);
    } catch (err) {
      setError('Failed to load complaints');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComplaints();
  }, [page, categoryFilter, priorityFilter, statusFilter]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getPriorityClass = (priority: string) => {
    return `priority-${priority.toLowerCase()}`;
  };

  const getStatusClass = (status: string) => {
    return `status-${status.toLowerCase().replace('_', '-')}`;
  };

  if (loading && complaints.length === 0) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  return (
    <div className="complaint-list">
      <h2>Complaints ({total})</h2>

      <div className="filters">
        <select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All Categories</option>
          <option value="water">Water</option>
          <option value="electricity">Electricity</option>
          <option value="sanitation">Sanitation</option>
          <option value="roads">Roads</option>
          <option value="streetlights">Streetlights</option>
          <option value="other">Other</option>
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => {
            setPriorityFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All Priorities</option>
          <option value="high">High</option>
          <option value="normal">Normal</option>
          <option value="low">Low</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="complaints-grid">
        {complaints.map((complaint) => (
          <div key={complaint.id} className="complaint-card">
            <div className="complaint-header">
              <span className={getPriorityClass(complaint.priority)}>
                {complaint.priority.toUpperCase()}
              </span>
              <span className={getStatusClass(complaint.status)}>
                {complaint.status.replace('_', ' ')}
              </span>
            </div>

            <div className="complaint-body">
              <p className="complaint-category">
                <strong>{complaint.category}</strong>
              </p>
              <p className="complaint-location">📍 {complaint.location}</p>
              <p className="complaint-text">
                {complaint.ai_summary || complaint.text.substring(0, 150)}
                {complaint.text.length > 150 && !complaint.ai_summary && '...'}
              </p>
            </div>

            <div className="complaint-footer">
              <small>Created: {formatDate(complaint.created_at)}</small>
              <small>Triaged by: {complaint.triaged_by}</small>
            </div>
          </div>
        ))}
      </div>

      {complaints.length === 0 && <p>No complaints found.</p>}

      <div className="pagination">
        <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>
          Previous
        </button>
        <span>
          Page {page} of {Math.ceil(total / 20) || 1}
        </span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={page >= Math.ceil(total / 20)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
