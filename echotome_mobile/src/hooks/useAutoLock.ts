/**
 * useAutoLock Hook (v3.1)
 *
 * Automatically locks sessions when app goes to background.
 * Behavior depends on profile's auto_lock_on_background setting.
 */

import { useEffect, useRef, useCallback } from 'react';
import { AppState, AppStateStatus, Alert } from 'react-native';
import { getApiClient } from '../api/client';
import type { PrivacyProfile } from '../api/types';

interface UseAutoLockOptions {
  enabled?: boolean;
  profile?: PrivacyProfile;
  sessionId?: string;
  onLocked?: () => void;
  gracePeriodMs?: number;
}

// Profile-specific auto-lock behavior
const PROFILE_AUTO_LOCK: Record<PrivacyProfile, { autoLock: boolean; gracePeriodMs: number }> = {
  'Quick Lock': { autoLock: false, gracePeriodMs: 0 },
  'Ritual Lock': { autoLock: true, gracePeriodMs: 5000 }, // 5 second grace
  'Black Vault': { autoLock: true, gracePeriodMs: 0 }, // Immediate
};

export function useAutoLock({
  enabled = true,
  profile = 'Ritual Lock',
  sessionId,
  onLocked,
  gracePeriodMs,
}: UseAutoLockOptions = {}) {
  const appState = useRef(AppState.currentState);
  const backgroundTime = useRef<number | null>(null);
  const lockTimeout = useRef<NodeJS.Timeout | null>(null);

  const profileConfig = PROFILE_AUTO_LOCK[profile];
  const effectiveGracePeriod = gracePeriodMs ?? profileConfig.gracePeriodMs;
  const shouldAutoLock = enabled && profileConfig.autoLock;

  const lockSession = useCallback(async () => {
    if (!sessionId) return;

    try {
      const client = getApiClient();
      await client.endSession(sessionId, true);
      onLocked?.();
    } catch (error) {
      console.error('[AutoLock] Failed to lock session:', error);
    }
  }, [sessionId, onLocked]);

  const handleAppStateChange = useCallback(
    (nextAppState: AppStateStatus) => {
      if (!shouldAutoLock || !sessionId) {
        appState.current = nextAppState;
        return;
      }

      // App going to background
      if (appState.current === 'active' && nextAppState.match(/inactive|background/)) {
        backgroundTime.current = Date.now();

        if (effectiveGracePeriod > 0) {
          // Start grace period timer
          lockTimeout.current = setTimeout(() => {
            lockSession();
          }, effectiveGracePeriod);
        } else {
          // Immediate lock (Black Vault)
          lockSession();
        }
      }

      // App coming back to foreground
      if (appState.current.match(/inactive|background/) && nextAppState === 'active') {
        // Cancel pending lock if within grace period
        if (lockTimeout.current) {
          clearTimeout(lockTimeout.current);
          lockTimeout.current = null;
        }

        // Check if we were gone too long
        if (backgroundTime.current) {
          const elapsed = Date.now() - backgroundTime.current;
          // If we're returning after the grace period, the session should already be locked
          // Just log for debugging
          if (elapsed > effectiveGracePeriod && effectiveGracePeriod > 0) {
            console.log('[AutoLock] Returned after grace period expired');
          }
        }
        backgroundTime.current = null;
      }

      appState.current = nextAppState;
    },
    [shouldAutoLock, sessionId, effectiveGracePeriod, lockSession]
  );

  useEffect(() => {
    const subscription = AppState.addEventListener('change', handleAppStateChange);

    return () => {
      subscription.remove();
      if (lockTimeout.current) {
        clearTimeout(lockTimeout.current);
      }
    };
  }, [handleAppStateChange]);

  // Manual lock function
  const lock = useCallback(() => {
    lockSession();
  }, [lockSession]);

  return {
    lock,
    isAutoLockEnabled: shouldAutoLock,
    gracePeriodMs: effectiveGracePeriod,
  };
}

export default useAutoLock;
