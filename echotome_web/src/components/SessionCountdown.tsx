'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/api/client';
import type { Session, PrivacyProfile } from '@/api/types';

interface SessionCountdownProps {
  session: Session;
  onExpired?: () => void;
  onExtended?: () => void;
}

const maxExtendMap: Record<PrivacyProfile, number> = {
  'Quick Lock': 1800,
  'Ritual Lock': 900,
  'Black Vault': 300,
};

export function SessionCountdown({ session, onExpired, onExtended }: SessionCountdownProps) {
  const [timeRemaining, setTimeRemaining] = useState(session.time_remaining);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          onExpired?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [onExpired]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const getColor = () => {
    if (timeRemaining <= 60) return 'var(--danger)';
    if (timeRemaining <= 300) return 'var(--warning)';
    return 'var(--success)';
  };

  const handleExtend = async () => {
    const maxExtend = maxExtendMap[session.profile];
    await apiClient.extendSession(session.session_id, maxExtend);
    setTimeRemaining(prev => Math.min(prev + maxExtend, maxExtendMap[session.profile] * 2));
    onExtended?.();
  };

  const handleLock = async () => {
    await apiClient.endSession(session.session_id);
    onExpired?.();
  };

  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '1rem',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
        Session expires in
      </div>
      <div style={{
        fontSize: '2.5rem',
        fontWeight: 700,
        fontFamily: 'monospace',
        color: getColor(),
      }}>
        {formatTime(timeRemaining)}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', justifyContent: 'center' }}>
        <button className="btn btn-outline" onClick={handleExtend}>Extend</button>
        <button className="btn btn-danger" onClick={handleLock}>Lock Now</button>
      </div>
    </div>
  );
}

export default SessionCountdown;
