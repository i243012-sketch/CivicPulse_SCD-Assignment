import { useState } from 'react';
import { ComplaintForm } from '../components/ComplaintForm';
import { ComplaintList } from '../components/ComplaintList';
import { Dashboard } from '../components/Dashboard';

export function HomePage() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleComplaintSuccess = () => {
    // Trigger refresh of complaint list and dashboard
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="home-page">
      <header>
        <h1>CivicPulse</h1>
        <p>Municipal Complaint Intake & Triage System</p>
      </header>

      <main>
        <div className="main-content">
          <section className="form-section">
            <ComplaintForm onSuccess={handleComplaintSuccess} />
          </section>

          <section className="dashboard-section">
            <Dashboard key={refreshKey} />
          </section>
        </div>

        <section className="list-section">
          <ComplaintList key={refreshKey} />
        </section>
      </main>
    </div>
  );
}
