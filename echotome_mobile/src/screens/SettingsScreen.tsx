/**
 * Echotome Mobile v3.0 SettingsScreen
 *
 * App settings and configuration
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { Button } from '../components/Button';
import { FormField } from '../components/FormField';
import { validateApiUrl } from '../utils/validation';
import { getApiClient } from '../api/client';
import { API_CONFIG, STORAGE_KEYS } from '../config/env';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'Settings'>;

export function SettingsScreen({ navigation }: Props) {
  const [apiUrl, setApiUrl] = useState(API_CONFIG.DEFAULT_BASE_URL);
  const [urlError, setUrlError] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<'unknown' | 'healthy' | 'error'>('unknown');
  const [vaultCount, setVaultCount] = useState<number>(0);

  useEffect(() => {
    loadSettings();
    checkHealth();
  }, []);

  const loadSettings = async () => {
    try {
      const savedUrl = await AsyncStorage.getItem(STORAGE_KEYS.API_BASE_URL);
      if (savedUrl) {
        setApiUrl(savedUrl);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const checkHealth = async () => {
    try {
      const apiClient = getApiClient();
      await apiClient.health();
      setHealthStatus('healthy');

      // Get vault count
      const vaults = await apiClient.listVaults();
      setVaultCount(vaults.length);
    } catch (error) {
      setHealthStatus('error');
    }
  };

  const handleSaveUrl = async () => {
    const validation = validateApiUrl(apiUrl);
    if (!validation.valid) {
      setUrlError(validation.error);
      return;
    }

    setUrlError(undefined);
    setLoading(true);

    try {
      // Save to AsyncStorage
      await AsyncStorage.setItem(STORAGE_KEYS.API_BASE_URL, apiUrl);

      // Update API client
      const apiClient = getApiClient(apiUrl);

      // Test connection
      await apiClient.health();

      Alert.alert('Success', 'API URL updated successfully');
      setHealthStatus('healthy');

      // Refresh vault count
      const vaults = await apiClient.listVaults();
      setVaultCount(vaults.length);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to connect to API';
      Alert.alert('Connection Error', message);
      setHealthStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetUrl = async () => {
    Alert.alert(
      'Reset API URL',
      'Reset to default API URL?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Reset',
          onPress: async () => {
            setApiUrl(API_CONFIG.DEFAULT_BASE_URL);
            await AsyncStorage.setItem(STORAGE_KEYS.API_BASE_URL, API_CONFIG.DEFAULT_BASE_URL);
            getApiClient(API_CONFIG.DEFAULT_BASE_URL);
            checkHealth();
          },
        },
      ]
    );
  };

  const getHealthStatusColor = () => {
    switch (healthStatus) {
      case 'healthy':
        return colors.success;
      case 'error':
        return colors.danger;
      default:
        return colors.textTertiary;
    }
  };

  const getHealthStatusText = () => {
    switch (healthStatus) {
      case 'healthy':
        return '✓ Connected';
      case 'error':
        return '✗ Not Connected';
      default:
        return '● Unknown';
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>Settings</Text>

        {/* API Configuration */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>API Configuration</Text>

          <FormField
            label="API Base URL"
            placeholder="http://10.0.2.2:8000"
            value={apiUrl}
            onChangeText={(text) => {
              setApiUrl(text);
              setUrlError(undefined);
            }}
            error={urlError}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />

          <View style={styles.buttonRow}>
            <Button
              title="Save"
              onPress={handleSaveUrl}
              variant="primary"
              loading={loading}
              disabled={loading}
              style={styles.button}
            />

            <Button
              title="Reset"
              onPress={handleResetUrl}
              variant="secondary"
              disabled={loading}
              style={styles.button}
            />
          </View>

          <View style={styles.urlHints}>
            <Text style={styles.hintTitle}>Common URLs:</Text>
            <Text style={styles.hint}>• Emulator: {API_CONFIG.DEFAULT_BASE_URL}</Text>
            <Text style={styles.hint}>• Localhost: {API_CONFIG.LOCALHOST}</Text>
            <Text style={styles.hint}>• Device: http://YOUR_PC_IP:8000</Text>
          </View>
        </View>

        {/* Status */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Status</Text>

          <View style={styles.statusCard}>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>API Connection</Text>
              <Text style={[styles.statusValue, { color: getHealthStatusColor() }]}>
                {getHealthStatusText()}
              </Text>
            </View>

            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Vaults</Text>
              <Text style={styles.statusValue}>{vaultCount}</Text>
            </View>

            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>App Version</Text>
              <Text style={styles.statusValue}>3.0.0</Text>
            </View>
          </View>

          <Button
            title="Refresh Status"
            onPress={checkHealth}
            variant="ghost"
            fullWidth
          />
        </View>

        {/* About */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About Echotome</Text>

          <View style={styles.aboutCard}>
            <Text style={styles.aboutText}>
              Echotome v3.0 — Ritual Cryptography Engine
            </Text>
            <Text style={styles.aboutText}>
              A cryptographic system that binds encryption keys to the temporal playback of audio,
              creating rituals that can only be performed in real-time.
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  scrollView: {
    flex: 1,
  },

  scrollContent: {
    padding: spacing.md,
  },

  title: {
    ...typography.title,
    color: colors.textPrimary,
    marginBottom: spacing.lg,
  },

  section: {
    marginBottom: spacing.xl,
  },

  sectionTitle: {
    ...typography.heading,
    color: colors.textPrimary,
    marginBottom: spacing.md,
  },

  buttonRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },

  button: {
    flex: 1,
  },

  urlHints: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },

  hintTitle: {
    ...typography.captionBold,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },

  hint: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: 2,
  },

  statusCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },

  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },

  statusLabel: {
    ...typography.body,
    color: colors.textSecondary,
  },

  statusValue: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },

  aboutCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },

  aboutText: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
});
