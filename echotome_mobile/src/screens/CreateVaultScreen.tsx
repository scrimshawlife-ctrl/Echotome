/**
 * Echotome Mobile v3.0 CreateVaultScreen
 *
 * Form for creating a new vault with name and profile selection
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { colors, getProfileColor, getProfileBackground } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { FormField } from '../components/FormField';
import { Button } from '../components/Button';
import { PrivacyPill } from '../components/PrivacyPill';
import { validateVaultName } from '../utils/validation';
import { PROFILE_CONFIG } from '../config/env';
import { getApiClient } from '../api/client';
import type { PrivacyProfile } from '../api/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'CreateVault'>;

export function CreateVaultScreen({ navigation }: Props) {
  const [name, setName] = useState('');
  const [profile, setProfile] = useState<PrivacyProfile>('Ritual Lock');
  const [nameError, setNameError] = useState<string>();
  const [loading, setLoading] = useState(false);

  const profiles: PrivacyProfile[] = ['Quick Lock', 'Ritual Lock', 'Black Vault'];

  const handleSubmit = async () => {
    // Validate name
    const validation = validateVaultName(name);
    if (!validation.valid) {
      setNameError(validation.error);
      return;
    }

    setNameError(undefined);
    setLoading(true);

    try {
      const apiClient = getApiClient();
      const response = await apiClient.createVault({ name, profile });

      Alert.alert('Vault Created', response.message || 'Vault created successfully');

      // Navigate to bind ritual screen
      navigation.replace('BindRitual', {
        vaultId: response.vault.id,
        vaultName: response.vault.name,
        profile: response.vault.profile,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create vault';
      Alert.alert('Error', message);
      setLoading(false);
    }
  };

  const renderProfileCard = (prof: PrivacyProfile) => {
    const config = PROFILE_CONFIG[prof.replace(' ', '_').toUpperCase() as keyof typeof PROFILE_CONFIG];
    const isSelected = profile === prof;

    return (
      <TouchableOpacity
        key={prof}
        style={[
          styles.profileCard,
          isSelected && {
            borderColor: getProfileColor(prof),
            backgroundColor: getProfileBackground(prof),
          },
        ]}
        onPress={() => setProfile(prof)}
        activeOpacity={0.7}
      >
        <View style={styles.profileHeader}>
          <Text style={styles.profileEmoji}>{config.emoji}</Text>
          <PrivacyPill profile={prof} size="small" />
        </View>

        <Text style={styles.profileDescription}>{config.description}</Text>

        <View style={styles.profileStats}>
          <Text style={styles.profileStat}>
            🎵 Audio: {Math.round(config.audioDependence * 100)}%
          </Text>
          <Text style={styles.profileStat}>
            ⏱️ Timing: {config.timingEnforcement ? 'Yes' : 'No'}
          </Text>
          <Text style={styles.profileStat}>
            🎤 Mic: {config.microphoneRequired ? 'Required' : 'Optional'}
          </Text>
        </View>
      </TouchableOpacity>
    );
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
        <Text style={styles.title}>Create New Vault</Text>
        <Text style={styles.subtitle}>
          Choose a name and privacy profile for your vault
        </Text>

        <FormField
          label="Vault Name"
          placeholder="Enter vault name"
          value={name}
          onChangeText={(text) => {
            setName(text);
            setNameError(undefined);
          }}
          error={nameError}
          autoCapitalize="words"
          returnKeyType="next"
        />

        <Text style={styles.sectionTitle}>Privacy Profile</Text>
        {profiles.map(renderProfileCard)}

        <Button
          title="Create Vault"
          onPress={handleSubmit}
          variant="primary"
          fullWidth
          loading={loading}
          disabled={loading || !name.trim()}
        />
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
    marginBottom: spacing.xs,
  },

  subtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },

  sectionTitle: {
    ...typography.heading,
    color: colors.textPrimary,
    marginBottom: spacing.md,
    marginTop: spacing.sm,
  },

  profileCard: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 2,
    borderColor: colors.border,
  },

  profileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },

  profileEmoji: {
    fontSize: 32,
  },

  profileDescription: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },

  profileStats: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },

  profileStat: {
    ...typography.caption,
    color: colors.textTertiary,
    marginRight: spacing.md,
  },
});
