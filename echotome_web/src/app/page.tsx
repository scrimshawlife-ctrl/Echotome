'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import type { Vault, Session } from '@/api/types';

export default function HomePage() {
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiClient.listVaults().catch(() => []),
      apiClient.listSessions().catch(() => []),
    ]).then(([v, s]) => {
      setVaults(v);
      setSessions(s);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="container text-center mt-2">Loading...</div>;
  }

  return (
    <div className="container">
      <h1 className="mb-2">Dashboard</h1>

      <div className="grid grid-2">
        <div className="card">
          <h2 className="mb-1">Vaults</h2>
          <p className="text-secondary mb-2">{vaults.length} vault(s)</p>
          <a href="/vaults" className="btn btn-primary">Manage Vaults</a>
        </div>

        <div className="card">
          <h2 className="mb-1">Active Sessions</h2>
          <p className="text-secondary mb-2">{sessions.length} active session(s)</p>
          <a href="/sessions" className="btn btn-outline">View Sessions</a>
        </div>
      </div>

      <div className="card mt-2">
        <h2 className="mb-1">Privacy Profiles</h2>
        <div className="grid grid-2 mt-2">
          <div className="card" style={{ borderColor: 'var(--quick-lock)' }}>
            <span className="badge badge-quick">Quick Lock</span>
            <p className="text-sm text-secondary mt-1">TM-CASUAL: Casual snooping protection. 30min sessions.</p>
          </div>
          <div className="card" style={{ borderColor: 'var(--ritual-lock)' }}>
            <span className="badge badge-ritual">Ritual Lock</span>
            <p className="text-sm text-secondary mt-1">TM-TARGETED: Targeted attack resistance. 15min sessions.</p>
          </div>
          <div className="card" style={{ borderColor: 'var(--black-vault)' }}>
            <span className="badge badge-black">Black Vault</span>
            <p className="text-sm text-secondary mt-1">TM-COERCION: Deniable encryption. 5min sessions.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
