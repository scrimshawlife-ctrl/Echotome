/**
 * Echotome Mobile v3.0 VaultListScreen
 *
 * Displays list of all vaults with refresh capability
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  FlatList,
  Text,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { VaultCard } from '../components/VaultCard';
import { getApiClient } from '../api/client';
import type { Vault } from '../api/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'VaultList'>;

export function VaultListScreen({ navigation }: Props) {
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string>();

  const loadVaults = useCallback(async () => {
    try {
      setError(undefined);
      const apiClient = getApiClient();
      const data = await apiClient.listVaults();
      setVaults(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load vaults';
      setError(message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadVaults();
  }, [loadVaults]);

  useEffect(() => {
    // Refresh when screen comes into focus
    const unsubscribe = navigation.addListener('focus', () => {
      loadVaults();
    });

    return unsubscribe;
  }, [navigation, loadVaults]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadVaults();
  };

  const handleVaultPress = (vault: Vault) => {
    navigation.navigate('VaultDetail', { vaultId: vault.id });
  };

  const handleCreateVault = () => {
    navigation.navigate('CreateVault');
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <Text style={styles.emptyIcon}>🔮</Text>
      <Text style={styles.emptyTitle}>No Vaults Yet</Text>
      <Text style={styles.emptyText}>
        Create your first vault to begin your journey into Ritual Cryptography
      </Text>
      <TouchableOpacity style={styles.emptyButton} onPress={handleCreateVault}>
        <Text style={styles.emptyButtonText}>Create First Vault</Text>
      </TouchableOpacity>
    </View>
  );

  const renderError = () => (
    <View style={styles.errorState}>
      <Text style={styles.errorIcon}>⚠️</Text>
      <Text style={styles.errorTitle}>Connection Error</Text>
      <Text style={styles.errorText}>{error}</Text>
      <TouchableOpacity style={styles.retryButton} onPress={loadVaults}>
        <Text style={styles.retryButtonText}>Retry</Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={styles.loadingText}>Loading vaults…</Text>
      </View>
    );
  }

  if (error && vaults.length === 0) {
    return <View style={styles.container}>{renderError()}</View>;
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={vaults}
        renderItem={({ item }) => (
          <VaultCard vault={item} onPress={() => handleVaultPress(item)} />
        )}
        keyExtractor={(item) => item.id}
        contentContainerStyle={[
          styles.listContent,
          vaults.length === 0 && styles.listContentEmpty,
        ]}
        ListEmptyComponent={renderEmptyState}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      />

      {/* FAB */}
      <TouchableOpacity style={styles.fab} onPress={handleCreateVault}>
        <Text style={styles.fabIcon}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
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

  listContent: {
    padding: spacing.md,
  },

  listContentEmpty: {
    flex: 1,
  },

  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },

  emptyIcon: {
    fontSize: 64,
    marginBottom: spacing.md,
  },

  emptyTitle: {
    ...typography.title,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },

  emptyText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },

  emptyButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: 8,
  },

  emptyButtonText: {
    ...typography.button,
    color: colors.textPrimary,
  },

  errorState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },

  errorIcon: {
    fontSize: 64,
    marginBottom: spacing.md,
  },

  errorTitle: {
    ...typography.title,
    color: colors.danger,
    marginBottom: spacing.sm,
  },

  errorText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },

  retryButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: 8,
  },

  retryButtonText: {
    ...typography.button,
    color: colors.textPrimary,
  },

  fab: {
    position: 'absolute',
    right: spacing.lg,
    bottom: spacing.lg,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },

  fabIcon: {
    fontSize: 32,
    color: colors.textPrimary,
    fontWeight: '300',
  },
});
