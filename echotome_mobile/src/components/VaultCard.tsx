/**
 * Echotome Mobile v3.0 VaultCard Component
 *
 * Card displaying vault information in list view
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';
import { spacing, componentSpacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { formatRelativeTime, shortenRuneId } from '../utils/formatting';
import { PrivacyPill } from './PrivacyPill';
import type { Vault } from '../api/types';

export interface VaultCardProps {
  vault: Vault;
  onPress: () => void;
}

export function VaultCard({ vault, onPress }: VaultCardProps) {
  return (
    <TouchableOpacity
      style={styles.container}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <Text style={styles.name} numberOfLines={1}>
          {vault.name}
        </Text>
        <PrivacyPill profile={vault.profile} size="small" />
      </View>

      <View style={styles.metadata}>
        <Text style={styles.runeId}>{shortenRuneId(vault.rune_id)}</Text>
        {vault.has_certificate && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>🔮 Ritual Bound</Text>
          </View>
        )}
      </View>

      <View style={styles.footer}>
        <Text style={styles.timestamp}>
          {formatRelativeTime(vault.updated_at)}
        </Text>
        {vault.encrypted_files && vault.encrypted_files.length > 0 && (
          <Text style={styles.fileCount}>
            {vault.encrypted_files.length} {vault.encrypted_files.length === 1 ? 'file' : 'files'}
          </Text>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: componentSpacing.cardBorderRadius,
    padding: componentSpacing.cardPadding,
    marginBottom: componentSpacing.cardMargin,
    borderWidth: 1,
    borderColor: colors.border,
  },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },

  name: {
    ...typography.subtitle,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },

  metadata: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },

  runeId: {
    ...typography.caption,
    color: colors.textSecondary,
    fontFamily: 'monospace',
  },

  badge: {
    backgroundColor: colors.accentDark + '30',
    borderRadius: componentSpacing.pillBorderRadius,
    paddingVertical: 2,
    paddingHorizontal: 8,
    marginLeft: spacing.sm,
  },

  badgeText: {
    ...typography.small,
    color: colors.accent,
  },

  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  timestamp: {
    ...typography.caption,
    color: colors.textTertiary,
  },

  fileCount: {
    ...typography.caption,
    color: colors.textSecondary,
  },
});
