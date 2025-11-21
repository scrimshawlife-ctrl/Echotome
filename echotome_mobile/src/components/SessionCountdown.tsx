/**
 * SessionCountdown Component (v3.1)
 *
 * Displays countdown timer for active ritual sessions.
 * Auto-updates every second and provides lock/extend actions.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { getApiClient } from '../api/client';
import type { Session, SessionInfo } from '../api/types';

interface SessionCountdownProps {
  session: Session | SessionInfo;
  vaultId: string;
  onSessionEnd?: () => void;
  onSessionExtended?: (newTimeRemaining: number) => void;
  compact?: boolean;
}

/**
 * Format seconds to MM:SS
 */
function formatTime(seconds: number): string {
  if (seconds <= 0) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Get color based on time remaining
 */
function getTimeColor(seconds: number): string {
  if (seconds <= 60) return colors.error; // Red: < 1 min
  if (seconds <= 300) return colors.warning; // Orange: < 5 min
  return colors.success; // Green: > 5 min
}

export const SessionCountdown: React.FC<SessionCountdownProps> = ({
  session,
  vaultId,
  onSessionEnd,
  onSessionExtended,
  compact = false,
}) => {
  const [timeRemaining, setTimeRemaining] = useState(session.time_remaining);
  const [isLocking, setIsLocking] = useState(false);
  const [isExtending, setIsExtending] = useState(false);

  // Get session_id from either Session or SessionInfo
  const sessionId = 'session_id' in session ? session.session_id : '';

  // Countdown timer
  useEffect(() => {
    if (timeRemaining <= 0) {
      onSessionEnd?.();
      return;
    }

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        const next = prev - 1;
        if (next <= 0) {
          clearInterval(interval);
          onSessionEnd?.();
          return 0;
        }
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeRemaining, onSessionEnd]);

  // Lock session handler
  const handleLock = useCallback(async () => {
    if (!sessionId) return;

    Alert.alert(
      'Lock Vault',
      'This will end your session and securely delete all decrypted content.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Lock Now',
          style: 'destructive',
          onPress: async () => {
            setIsLocking(true);
            try {
              const client = getApiClient();
              await client.endSession(sessionId, true);
              onSessionEnd?.();
            } catch (error) {
              Alert.alert('Error', 'Failed to lock vault');
            } finally {
              setIsLocking(false);
            }
          },
        },
      ]
    );
  }, [sessionId, onSessionEnd]);

  // Extend session handler
  const handleExtend = useCallback(async () => {
    if (!sessionId) return;

    setIsExtending(true);
    try {
      const client = getApiClient();
      const response = await client.extendSession(sessionId, 300); // +5 minutes
      setTimeRemaining(response.time_remaining);
      onSessionExtended?.(response.time_remaining);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to extend session');
    } finally {
      setIsExtending(false);
    }
  }, [sessionId, onSessionExtended]);

  const timeColor = getTimeColor(timeRemaining);
  const isExpired = timeRemaining <= 0;

  if (compact) {
    return (
      <View style={styles.compactContainer}>
        <View style={[styles.statusDot, { backgroundColor: timeColor }]} />
        <Text style={[styles.compactTime, { color: timeColor }]}>
          {isExpired ? 'EXPIRED' : formatTime(timeRemaining)}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={[styles.statusDot, { backgroundColor: timeColor }]} />
        <Text style={styles.label}>Session Active</Text>
      </View>

      <Text style={[styles.countdown, { color: timeColor }]}>
        {isExpired ? 'EXPIRED' : formatTime(timeRemaining)}
      </Text>

      <Text style={styles.hint}>
        {isExpired
          ? 'Session has ended'
          : timeRemaining <= 60
          ? 'Session ending soon!'
          : 'Vault unlocked'}
      </Text>

      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.button, styles.extendButton]}
          onPress={handleExtend}
          disabled={isExtending || isExpired}
        >
          <Text style={styles.buttonText}>
            {isExtending ? 'Extending...' : '+5 min'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.lockButton]}
          onPress={handleLock}
          disabled={isLocking || isExpired}
        >
          <Text style={[styles.buttonText, styles.lockButtonText]}>
            {isLocking ? 'Locking...' : 'Lock Now'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginVertical: spacing.sm,
    alignItems: 'center',
  },
  compactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.xs,
  },
  label: {
    fontSize: 14,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  countdown: {
    fontSize: 48,
    fontWeight: 'bold',
    fontVariant: ['tabular-nums'],
  },
  compactTime: {
    fontSize: 14,
    fontWeight: '600',
    fontVariant: ['tabular-nums'],
  },
  hint: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: spacing.xs,
    marginBottom: spacing.md,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  button: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 8,
    minWidth: 100,
    alignItems: 'center',
  },
  extendButton: {
    backgroundColor: colors.primary,
  },
  lockButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.error,
  },
  buttonText: {
    color: colors.background,
    fontSize: 14,
    fontWeight: '600',
  },
  lockButtonText: {
    color: colors.error,
  },
});

export default SessionCountdown;
