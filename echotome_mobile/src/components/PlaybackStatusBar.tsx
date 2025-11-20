/**
 * Echotome Mobile v3.0 PlaybackStatusBar Component
 *
 * Shows progress bar and status during ritual playback
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';

export interface PlaybackStatusBarProps {
  progress: number; // 0-100
  status: string;
  error?: string;
}

export function PlaybackStatusBar({
  progress,
  status,
  error,
}: PlaybackStatusBarProps) {
  return (
    <View style={styles.container}>
      {/* Progress bar */}
      <View style={styles.progressContainer}>
        <View style={[styles.progressBar, { width: `${progress}%` }]} />
      </View>

      {/* Status text */}
      <Text style={[styles.status, error && styles.statusError]}>
        {error || status}
      </Text>

      {/* Progress percentage */}
      {!error && (
        <Text style={styles.percentage}>{Math.round(progress)}%</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: spacing.md,
  },

  progressContainer: {
    height: 4,
    backgroundColor: colors.surface,
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: spacing.sm,
  },

  progressBar: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: 2,
  },

  status: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },

  statusError: {
    color: colors.danger,
  },

  percentage: {
    ...typography.caption,
    color: colors.textTertiary,
    textAlign: 'center',
  },
});
