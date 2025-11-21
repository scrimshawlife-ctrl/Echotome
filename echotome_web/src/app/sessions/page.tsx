'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import type { Session, PrivacyProfile } from '@/api/types';

const profileBadgeClass: Record<PrivacyProfile, string> = {
  'Quick Lock': 'badge-quick',
  'Ritual Lock': 'badge-ritual',
  'Black Vault': 'badge-black',
};

export default function SessionsPage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSessions = () => {
    apiClient.listSessions().then(setSessions).catch(() => setSessions([])).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSessions();
    const interval = setInterval(loadSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleEnd = async (id: string) => {
    await apiClient.endSession(id);
    setSessions(sessions.filter(s => s.session_id !== id));
  };

  const handleEndAll = async () => {
    if (!confirm('End all active sessions?')) return;
    await apiClient.endAllSessions();
    setSessions([]);
  };

  const handleExtend = async (id: string) => {
    const session = sessions.find(s => s.session_id === id);
    if (!session) return;
    const maxExtend = session.profile === 'Black Vault' ? 300 : session.profile === 'Ritual Lock' ? 900 : 1800;
    await apiClient.extendSession(id, maxExtend);
    loadSessions();
  };

  if (loading) return <div className="container text-center mt-2">Loading...</div>;

  return (
    <div className="container">
      <div className="flex flex-between flex-center mb-2">
        <h1>Active Sessions</h1>
        {sessions.length > 0 && (
          <button className="btn btn-danger" onClick={handleEndAll}>Lock All</button>
        )}
      </div>

      {sessions.length === 0 ? (
        <div className="card text-center">
          <p className="text-secondary">No active sessions.</p>
        </div>
      ) : (
        <div className="grid grid-2">
          {sessions.map(session => (
            <div key={session.session_id} className="card">
              <div className="flex flex-between flex-center mb-1">
                <span className="text-sm text-secondary">Vault: {session.vault_id.slice(0, 8)}...</span>
                <span className={`badge ${profileBadgeClass[session.profile]}`}>{session.profile}</span>
              </div>
              <div style={{
                fontSize: '2rem',
                fontWeight: 700,
                fontFamily: 'monospace',
                color: session.time_remaining <= 60 ? 'var(--danger)' : session.time_remaining <= 300 ? 'var(--warning)' : 'var(--success)',
              }}>
                {session.time_remaining_formatted}
              </div>
              <div className="flex gap-1 mt-2">
                <button className="btn btn-outline" onClick={() => handleExtend(session.session_id)}>Extend</button>
                <button className="btn btn-danger" onClick={() => handleEnd(session.session_id)}>Lock</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
