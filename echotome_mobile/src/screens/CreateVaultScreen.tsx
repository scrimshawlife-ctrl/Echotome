/**
 * Echotome Mobile v3.1 CreateVaultScreen
 *
 * Form for creating a new vault with name, profile selection,
 * threat model display, and recovery codes option.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Switch,
} from 'react-native';
import { colors, getProfileColor, getProfileBackground } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { FormField } from '../components/FormField';
import { Button } from '../components/Button';
import { PrivacyPill } from '../components/PrivacyPill';
import { RecoveryCodesModal } from '../components/RecoveryCodesModal';
import { validateVaultName } from '../utils/validation';
import { PROFILE_CONFIG } from '../config/env';
import { getApiClient } from '../api/client';
import type { PrivacyProfile, ProfileDetail } from '../api/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'CreateVault'>;

// Threat model info per profile
const THREAT_MODELS: Record<PrivacyProfile, { id: string; description: string }> = {
  'Quick Lock': {
    id: 'TM-CASUAL',
    description: 'Protection against casual snooping. Not designed for adversarial threats.',
  },
  'Ritual Lock': {
    id: 'TM-TARGETED',
    description: 'Protection against targeted attacks requiring both audio ritual and passphrase.',
  },
  'Black Vault': {
    id: 'TM-COERCION',
    description: 'Deniable encryption with anti-forensic measures. Plausible deniability under duress.',
  },
};

export function CreateVaultScreen({ navigation }: Props) {
  const [name, setName] = useState('');
  const [profile, setProfile] = useState<PrivacyProfile>('Ritual Lock');
  const [enableRecovery, setEnableRecovery] = useState(true);
  const [nameError, setNameError] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [showRecoveryCodes, setShowRecoveryCodes] = useState(false);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [createdVault, setCreatedVault] = useState<{ id: string; name: string; profile: PrivacyProfile } | null>(null);

  const profiles: PrivacyProfile[] = ['Quick Lock', 'Ritual Lock', 'Black Vault'];

  // Black Vault has recovery disabled by default
  useEffect(() => {
    if (profile === 'Black Vault') {
      setEnableRecovery(false);
    } else {
      setEnableRecovery(true);
    }
  }, [profile]);

  const handleSubmit = async () => {
    const validation = validateVaultName(name);
    if (!validation.valid) {
      setNameError(validation.error);
      return;
    }

    setNameError(undefined);
    setLoading(true);

    try {
      const apiClient = getApiClient();
      const response = await apiClient.createVault({
        name,
        profile,
        enable_recovery: enableRecovery,
      });

      const vault = response.vault;
      setCreatedVault({ id: vault.id, name: vault.name, profile: vault.profile });

      // Show recovery codes if enabled and returned
      if (enableRecovery && response.recovery_codes && response.recovery_codes.length > 0) {
        setRecoveryCodes(response.recovery_codes);
        setShowRecoveryCodes(true);
      } else {
        navigateToBindRitual(vault);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create vault';
      Alert.alert('Error', message);
      setLoading(false);
    }
  };

  const navigateToBindRitual = (vault: { id: string; name: string; profile: PrivacyProfile }) => {
    navigation.replace('BindRitual', {
      vaultId: vault.id,
      vaultName: vault.name,
      profile: vault.profile,
    });
  };

  const handleRecoveryCodesDismiss = () => {
    setShowRecoveryCodes(false);
    if (createdVault) {
      navigateToBindRitual(createdVault);
    }
  };

  const renderProfileCard = (prof: PrivacyProfile) => {
    const config = PROFILE_CONFIG[prof.replace(' ', '_').toUpperCase() as keyof typeof PROFILE_CONFIG];
    const threatModel = THREAT_MODELS[prof];
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

        {/* Threat Model (v3.1) */}
        <View style={styles.threatModel}>
          <Text style={styles.threatModelId}>{threatModel.id}</Text>
          <Text style={styles.threatModelDesc}>{threatModel.description}</Text>
        </View>

        <View style={styles.profileStats}>
          <Text style={styles.profileStat}>
            Audio: {Math.round(config.audioDependence * 100)}%
          </Text>
          <Text style={styles.profileStat}>
            Timing: {config.timingEnforcement ? 'Yes' : 'No'}
          </Text>
          <Text style={styles.profileStat}>
            Mic: {config.microphoneRequired ? 'Required' : 'Optional'}
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

        {/* Recovery Codes Toggle (v3.1) */}
        <View style={styles.recoverySection}>
          <View style={styles.recoveryHeader}>
            <Text style={styles.recoveryTitle}>Recovery Codes</Text>
            <Switch
              value={enableRecovery}
              onValueChange={setEnableRecovery}
              trackColor={{ false: colors.border, true: colors.primary }}
              thumbColor={colors.background}
            />
          </View>
          <Text style={styles.recoveryDescription}>
            {enableRecovery
              ? 'Generate one-time recovery codes for emergency access. Recommended for most users.'
              : profile === 'Black Vault'
              ? 'Disabled for Black Vault profile (maximum deniability).'
              : 'No recovery option - if you lose your ritual, vault contents are unrecoverable.'}
          </Text>
        </View>

        <Button
          title="Create Vault"
          onPress={handleSubmit}
          variant="primary"
          fullWidth
          loading={loading}
          disabled={loading || !name.trim()}
        />
      </ScrollView>

      {/* Recovery Codes Modal (v3.1) */}
      <RecoveryCodesModal
        visible={showRecoveryCodes}
        codes={recoveryCodes}
        vaultName={createdVault?.name || name}
        onDismiss={handleRecoveryCodesDismiss}
      />
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
  threatModel: {
    backgroundColor: 'rgba(0,0,0,0.2)',
    borderRadius: 6,
    padding: spacing.sm,
    marginBottom: spacing.sm,
  },
  threatModelId: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.primary,
    marginBottom: 2,
  },
  threatModelDesc: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 16,
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
  recoverySection: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  recoveryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  recoveryTitle: {
    ...typography.bodyBold,
    color: colors.textPrimary,
  },
  recoveryDescription: {
    ...typography.caption,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
