'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/api/client';
import type { Vault, PrivacyProfile } from '@/api/types';

const profileBadgeClass: Record<PrivacyProfile, string> = {
  'Quick Lock': 'badge-quick',
  'Ritual Lock': 'badge-ritual',
  'Black Vault': 'badge-black',
};

export default function VaultsPage() {
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.listVaults().then(setVaults).catch(() => setVaults([])).finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete vault "${name}"? This cannot be undone.`)) return;
    await apiClient.deleteVault(id);
    setVaults(vaults.filter(v => v.id !== id));
  };

  if (loading) return <div className="container text-center mt-2">Loading...</div>;

  return (
    <div className="container">
      <div className="flex flex-between flex-center mb-2">
        <h1>Vaults</h1>
        <a href="/vaults/create" className="btn btn-primary">Create Vault</a>
      </div>

      {vaults.length === 0 ? (
        <div className="card text-center">
          <p className="text-secondary">No vaults yet.</p>
          <a href="/vaults/create" className="btn btn-primary mt-2">Create Your First Vault</a>
        </div>
      ) : (
        <div className="grid grid-2">
          {vaults.map(vault => (
            <div key={vault.id} className="card">
              <div className="flex flex-between flex-center mb-1">
                <h3>{vault.name}</h3>
                <span className={`badge ${profileBadgeClass[vault.profile]}`}>{vault.profile}</span>
              </div>
              <p className="text-sm text-secondary mb-2">ID: {vault.id.slice(0, 8)}...</p>
              {vault.has_active_session && (
                <p className="text-sm" style={{ color: 'var(--success)' }}>Session active</p>
              )}
              <div className="flex gap-1 mt-2">
                <a href={`/vaults/${vault.id}`} className="btn btn-outline">Open</a>
                <button className="btn btn-danger" onClick={() => handleDelete(vault.id, vault.name)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
