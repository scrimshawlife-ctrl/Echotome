/**
 * Echotome Mobile v3.0 VaultDetailScreen
 *
 * View vault details with actions for encrypt/decrypt
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { Button } from '../components/Button';
import { PrivacyPill } from '../components/PrivacyPill';
import { SigilPreview } from '../components/SigilPreview';
import { formatDateTime, shortenRuneId } from '../utils/formatting';
import { getApiClient } from '../api/client';
import type { Vault } from '../api/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'VaultDetail'>;

export function VaultDetailScreen({ navigation, route }: Props) {
  const { vaultId } = route.params as { vaultId: string };

  const [vault, setVault] = useState<Vault>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    loadVaultDetails();
  }, [vaultId]);

  useEffect(() => {
    // Refresh when screen comes into focus
    const unsubscribe = navigation.addListener('focus', () => {
      loadVaultDetails();
    });

    return unsubscribe;
  }, [navigation, vaultId]);

  const loadVaultDetails = async () => {
    try {
      setError(undefined);
      const apiClient = getApiClient();
      const vaults = await apiClient.listVaults();
      const foundVault = vaults.find((v) => v.id === vaultId);

      if (!foundVault) {
        throw new Error('Vault not found');
      }

      setVault(foundVault);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load vault';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleEncrypt = () => {
    navigation.navigate('Encrypt', { vaultId });
  };

  const handleDecrypt = () => {
    if (!vault?.has_certificate) {
      Alert.alert(
        'Ritual Not Bound',
        'You must bind a ritual to this vault before you can unlock it.',
        [
          {
            text: 'Bind Now',
            onPress: () =>
              navigation.navigate('BindRitual', {
                vaultId: vault?.id,
                vaultName: vault?.name,
                profile: vault?.profile,
              }),
          },
          { text: 'Cancel', style: 'cancel' },
        ]
      );
      return;
    }

    navigation.navigate('Decrypt', { vaultId });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Loading vault…</Text>
      </View>
    );
  }

  if (error || !vault) {
    return (
      <View style={styles.errorContainer}>
        <Text style={styles.errorText}>{error || 'Vault not found'}</Text>
        <Button title="Go Back" onPress={() => navigation.goBack()} variant="primary" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.name}>{vault.name}</Text>
        <PrivacyPill profile={vault.profile} />
      </View>

      <View style={styles.sigilContainer}>
        <SigilPreview
          sigilUrl={vault.sigil_url}
          runeId={vault.rune_id}
          size="xl"
        />
      </View>

      <View style={styles.metadata}>
        <View style={styles.metadataRow}>
          <Text style={styles.metadataLabel}>Rune ID</Text>
          <Text style={styles.metadataValue}>{shortenRuneId(vault.rune_id)}</Text>
        </View>

        <View style={styles.metadataRow}>
          <Text style={styles.metadataLabel}>Created</Text>
          <Text style={styles.metadataValue}>
            {formatDateTime(vault.created_at)}
          </Text>
        </View>

        <View style={styles.metadataRow}>
          <Text style={styles.metadataLabel}>Last Updated</Text>
          <Text style={styles.metadataValue}>
            {formatDateTime(vault.updated_at)}
          </Text>
        </View>

        <View style={styles.metadataRow}>
          <Text style={styles.metadataLabel}>Ritual Status</Text>
          <Text
            style={[
              styles.metadataValue,
              vault.has_certificate ? styles.metadataValueSuccess : styles.metadataValueDanger,
            ]}
          >
            {vault.has_certificate ? '🔮 Ritual Bound' : '⚠️ Not Bound'}
          </Text>
        </View>

        {vault.encrypted_files && vault.encrypted_files.length > 0 && (
          <View style={styles.metadataRow}>
            <Text style={styles.metadataLabel}>Encrypted Files</Text>
            <Text style={styles.metadataValue}>
              {vault.encrypted_files.length} {vault.encrypted_files.length === 1 ? 'file' : 'files'}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.actions}>
        <Button
          title="Encrypt into Vault"
          onPress={handleEncrypt}
          variant="primary"
          fullWidth
        />

        <Button
          title="Unlock Vault"
          onPress={handleDecrypt}
          variant="secondary"
          fullWidth
        />

        {!vault.has_certificate && (
          <Button
            title="Bind Ritual"
            onPress={() =>
              navigation.navigate('BindRitual', {
                vaultId: vault.id,
                vaultName: vault.name,
                profile: vault.profile,
              })
            }
            variant="ghost"
            fullWidth
          />
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  content: {
    padding: spacing.md,
  },

  loadingContainer: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },

  loadingText: {
    ...typography.body,
    color: colors.textSecondary,
    marginTop: spacing.md,
  },

  errorContainer: {
    flex: 1,
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },

  errorText: {
    ...typography.body,
    color: colors.danger,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },

  name: {
    ...typography.title,
    color: colors.textPrimary,
    flex: 1,
    marginRight: spacing.sm,
  },

  sigilContainer: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },

  metadata: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },

  metadataRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },

  metadataLabel: {
    ...typography.body,
    color: colors.textSecondary,
  },

  metadataValue: {
    ...typography.bodyBold,
    color: colors.textPrimary,
    textAlign: 'right',
    flex: 1,
    marginLeft: spacing.md,
  },

  metadataValueSuccess: {
    color: colors.success,
  },

  metadataValueDanger: {
    color: colors.warning,
  },

  actions: {
    gap: spacing.sm,
  },
});
