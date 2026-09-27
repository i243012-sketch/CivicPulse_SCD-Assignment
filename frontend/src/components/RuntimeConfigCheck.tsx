import { useEffect, useState, ReactNode } from 'react';
import { api } from '../api/client';

interface Props {
  children: ReactNode;
}

export function RuntimeConfigCheck({ children }: Props) {
  const [isReady, setIsReady] = useState<boolean | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        // We add support for checkHealth in client.ts
        const isHealthy = await api.checkHealth(controller.signal);
        clearTimeout(timeoutId);
        
        if (isHealthy) {
          setIsReady(true);
        } else {
          setIsReady(false);
          setErrorDetails('Backend service is not healthy.');
        }
      } catch (err: any) {
        setIsReady(false);
        setErrorDetails(err.message || 'Failed to connect to backend.');
      }
    };

    checkBackend();
  }, []);

  if (isReady === null) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <p>Connecting to backend services...</p>
      </div>
    );
  }

  if (isReady === false) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <h2>Service Unavailable</h2>
        <p>Could not connect to the CivicPulse backend.</p>
        {errorDetails && <p style={{ color: 'red' }}>{errorDetails}</p>}
        <p>Please ensure all backend services (Docker) are running.</p>
        <button 
          onClick={() => window.location.reload()}
          style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}
        >
          Retry
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
