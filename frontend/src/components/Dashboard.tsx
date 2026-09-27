import { useEffect, useState } from 'react';
import { api, Stats } from '../api/client';

export function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const loadStats = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getStats(controller.signal);
        setStats(data);
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        setError('Failed to load statistics');
      } finally {
        setLoading(false);
      }
    };

    loadStats();

    let interval: ReturnType<typeof setInterval>;
    
    const startPolling = () => {
      interval = setInterval(() => {
        if (document.visibilityState === 'visible') {
          loadStats();
        }
      }, 30000);
    };

    startPolling();

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        loadStats();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      controller.abort();
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  if (loading) {
    return <div>Loading statistics...</div>;
  }

  if (error || !stats) {
    return <div className="error-message">{error || 'No data'}</div>;
  }

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>

      <div className="stats-container">
        <div className="stat-card total">
          <h3>Total Complaints</h3>
          <p className="stat-value">{stats.total_complaints}</p>
        </div>

        <div className="stat-section">
          <h3>By Category</h3>
          <div className="stat-grid">
            {stats.by_category.map((item) => (
              <div key={item.category} className="stat-item">
                <span className="stat-label">{item.category}</span>
                <span className="stat-count">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="stat-section">
          <h3>By Priority</h3>
          <div className="stat-grid">
            {stats.by_priority.map((item) => (
              <div
                key={item.priority}
                className={`stat-item priority-${item.priority.toLowerCase()}`}
              >
                <span className="stat-label">{item.priority}</span>
                <span className="stat-count">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
