/**
 * Echotome Mobile v3.0 BindRitualScreen
 *
 * Bind audio ritual to vault
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { Button } from '../components/Button';
import { PrivacyPill } from '../components/PrivacyPill';
import { AudioSelector } from '../components/AudioSelector';
import { getApiClient } from '../api/client';
import { getRitualModeRequirements } from '../utils/validation';
import type { FilePickerResult, PrivacyProfile } from '../api/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'BindRitual'>;

export function BindRitualScreen({ navigation, route }: Props) {
  const { vaultId, vaultName, profile } = route.params as {
    vaultId: string;
    vaultName: string;
    profile: PrivacyProfile;
  };

  const [audioFile, setAudioFile] = useState<FilePickerResult>();
  const [loading, setLoading] = useState(false);

  const showMicWarning = profile === 'Black Vault' || profile === 'Ritual Lock';

  const handleSubmit = async () => {
    if (!audioFile) {
      Alert.alert('No Audio Selected', 'Please select an audio track to bind');
      return;
    }

    setLoading(true);

    try {
      const apiClient = getApiClient();
      const response = await apiClient.bindRitual(vaultId, profile, audioFile);

      Alert.alert(
        'Ritual Bound',
        response.message || 'Your vault has been bound to the ritual audio',
        [
          {
            text: 'OK',
            onPress: () => navigation.replace('VaultDetail', { vaultId }),
          },
        ]
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to bind ritual';
      Alert.alert('Error', message);
      setLoading(false);
    }
  };

  const getProfileExplanation = () => {
    switch (profile) {
      case 'Quick Lock':
        return 'Track will be used as an aesthetic key. Upload unlock is allowed.';
      case 'Ritual Lock':
        return 'Track will be bound with timing enforcement. You must play the full track to unlock.';
      case 'Black Vault':
        return 'Microphone ritual is REQUIRED for unlock. You must perform the ritual live.';
      default:
        return '';
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
        <View style={styles.header}>
          <Text style={styles.title}>Bind Ritual</Text>
          <PrivacyPill profile={profile} />
        </View>

        <Text style={styles.vaultName}>{vaultName}</Text>

        <View style={styles.explanation}>
          <Text style={styles.explanationTitle}>What is Ritual Binding?</Text>
          <Text style={styles.explanationText}>
            Ritual binding creates a cryptographic connection between your vault and an audio track.
            The track becomes part of the key material used to protect your files.
          </Text>
        </View>

        <View style={styles.profileBehavior}>
          <Text style={styles.profileBehaviorTitle}>Profile Behavior</Text>
          <Text style={styles.profileBehaviorText}>{getProfileExplanation()}</Text>
          <Text style={styles.profileBehaviorRequirement}>
            {getRitualModeRequirements(profile)}
          </Text>
        </View>

        <AudioSelector
          onSelect={setAudioFile}
          selectedFile={audioFile}
          showWarning={showMicWarning}
          warningText={
            profile === 'Black Vault'
              ? 'You MUST play this track via microphone to unlock. File upload will not work.'
              : 'You may be required to play this track via microphone later.'
          }
        />

        <Button
          title="Bind Ritual"
          onPress={handleSubmit}
          variant="primary"
          fullWidth
          loading={loading}
          disabled={loading || !audioFile}
        />

        <Button
          title="Skip for Now"
          onPress={() => navigation.replace('VaultDetail', { vaultId })}
          variant="ghost"
          fullWidth
          disabled={loading}
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

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },

  title: {
    ...typography.title,
    color: colors.textPrimary,
  },

  vaultName: {
    ...typography.subtitle,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },

  explanation: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },

  explanationTitle: {
    ...typography.heading,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },

  explanationText: {
    ...typography.body,
    color: colors.textSecondary,
  },

  profileBehavior: {
    backgroundColor: colors.primary + '15',
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.primary + '40',
  },

  profileBehaviorTitle: {
    ...typography.heading,
    color: colors.primary,
    marginBottom: spacing.xs,
  },

  profileBehaviorText: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },

  profileBehaviorRequirement: {
    ...typography.caption,
    color: colors.textTertiary,
    fontStyle: 'italic',
  },
});
