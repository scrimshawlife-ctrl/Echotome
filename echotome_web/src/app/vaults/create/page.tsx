'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/api/client';
import { THREAT_MODELS, type PrivacyProfile } from '@/api/types';

const profiles: PrivacyProfile[] = ['Quick Lock', 'Ritual Lock', 'Black Vault'];

export default function CreateVaultPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [profile, setProfile] = useState<PrivacyProfile>('Ritual Lock');
  const [enableRecovery, setEnableRecovery] = useState(true);
  const [loading, setLoading] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      const res = await apiClient.createVault({
        name: name.trim(),
        profile,
        enable_recovery: enableRecovery,
      });

      if (res.recovery_codes && res.recovery_codes.length > 0) {
        setRecoveryCodes(res.recovery_codes);
      } else {
        router.push('/vaults');
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create vault');
      setLoading(false);
    }
  };

  if (recoveryCodes) {
    return (
      <div className="container" style={{ maxWidth: 500 }}>
        <div className="card">
          <h2 className="mb-1">Recovery Codes</h2>
          <p className="text-secondary mb-2">Save these codes now. They won't be shown again.</p>
          <div style={{ background: 'var(--background)', padding: '1rem', borderRadius: 8, fontFamily: 'monospace' }}>
            {recoveryCodes.map((code, i) => (
              <div key={code} style={{ padding: '0.25rem 0' }}>{i + 1}. {code}</div>
            ))}
          </div>
          <button className="btn btn-primary mt-2" style={{ width: '100%' }} onClick={() => {
            navigator.clipboard.writeText(recoveryCodes.join('\n'));
            alert('Copied to clipboard');
          }}>Copy All</button>
          <button className="btn btn-outline mt-1" style={{ width: '100%' }} onClick={() => router.push('/vaults')}>
            I've Saved My Codes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container" style={{ maxWidth: 600 }}>
      <h1 className="mb-2">Create Vault</h1>
      <form onSubmit={handleSubmit}>
        <div className="card">
          <label className="text-sm text-secondary">Vault Name</label>
          <input
            type="text"
            className="input mt-1"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="My Vault"
            required
          />
        </div>

        <div className="card">
          <label className="text-sm text-secondary mb-1" style={{ display: 'block' }}>Privacy Profile</label>
          {profiles.map(p => {
            const tm = THREAT_MODELS[p];
            const isSelected = profile === p;
            return (
              <div
                key={p}
                onClick={() => {
                  setProfile(p);
                  setEnableRecovery(p !== 'Black Vault');
                }}
                style={{
                  padding: '1rem',
                  border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                  borderRadius: 8,
                  marginBottom: '0.5rem',
                  cursor: 'pointer',
                  background: isSelected ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                }}
              >
                <strong>{p}</strong>
                <p className="text-sm text-secondary mt-1">{tm.id}: {tm.description}</p>
              </div>
            );
          })}
        </div>

        <div className="card flex flex-between flex-center">
          <div>
            <strong>Recovery Codes</strong>
            <p className="text-sm text-secondary">Generate one-time recovery codes</p>
          </div>
          <input
            type="checkbox"
            checked={enableRecovery}
            onChange={e => setEnableRecovery(e.target.checked)}
            style={{ width: 20, height: 20 }}
          />
        </div>

        <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading || !name.trim()}>
          {loading ? 'Creating...' : 'Create Vault'}
        </button>
      </form>
    </div>
  );
}
