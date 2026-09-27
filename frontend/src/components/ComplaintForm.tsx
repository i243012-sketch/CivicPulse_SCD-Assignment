import { FormEvent, useState } from 'react';
import { api, ApiError } from '../api/client';

interface ComplaintFormProps {
  onSuccess?: () => void;
}

export function ComplaintForm({ onSuccess }: ComplaintFormProps) {
  const [text, setText] = useState('');
  const [location, setLocation] = useState('');
  const [reporterContact, setReporterContact] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await api.createComplaint({
        text,
        location,
        reporter_contact: reporterContact || undefined,
      });
      setSuccess(true);
      setText('');
      setLocation('');
      setReporterContact('');
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to submit complaint');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="complaint-form">
      <h2>Submit a Complaint</h2>

      {error && <div className="error-message">{error}</div>}
      {success && (
        <div className="success-message">
          Complaint submitted successfully!
        </div>
      )}

      <div className="form-group">
        <label htmlFor="text">
          Complaint Description <span className="required">*</span>
        </label>
        <textarea
          id="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          minLength={10}
          maxLength={2000}
          rows={6}
          required
          placeholder="Describe the issue (10-2000 characters)"
        />
        <small>{text.length}/2000 characters</small>
      </div>

      <div className="form-group">
        <label htmlFor="location">
          Location <span className="required">*</span>
        </label>
        <input
          type="text"
          id="location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          minLength={3}
          maxLength={200}
          required
          placeholder="e.g., 123 Main St, Downtown"
        />
      </div>

      <div className="form-group">
        <label htmlFor="contact">Contact Information (optional)</label>
        <input
          type="text"
          id="contact"
          value={reporterContact}
          onChange={(e) => setReporterContact(e.target.value)}
          maxLength={200}
          placeholder="Email or phone number"
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Submitting...' : 'Submit Complaint'}
      </button>
    </form>
  );
}
