/**
 * Echotome Mobile v3.0 DecryptScreen
 *
 * Unlock vault with ritual verification
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
  TouchableOpacity,
} from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { Button } from '../components/Button';
import { AudioSelector } from '../components/AudioSelector';
import { AudioRitualControl } from '../components/AudioRitualControl';
import { SigilPreview } from '../components/SigilPreview';
import { isRitualModeAllowed } from '../utils/validation';
import { getApiClient } from '../api/client';
import type { FilePickerResult, RitualMode, Vault } from '../api/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'Decrypt'>;

export function DecryptScreen({ navigation, route }: Props) {
  const { vaultId } = route.params as { vaultId: string };

  const [vault, setVault] = useState<Vault>();
  const [ritualMode, setRitualMode] = useState<RitualMode>('file');
  const [audioFile, setAudioFile] = useState<FilePickerResult>();
  const [ritualStarted, setRitualStarted] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadVaultDetails();
  }, [vaultId]);

  const loadVaultDetails = async () => {
    try {
      const apiClient = getApiClient();
      const vaults = await apiClient.listVaults();
      const foundVault = vaults.find((v) => v.id === vaultId);

      if (!foundVault) {
        throw new Error('Vault not found');
      }

      setVault(foundVault);

      // Set default ritual mode based on profile
      if (foundVault.profile === 'Black Vault') {
        setRitualMode('mic');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load vault';
      Alert.alert('Error', message);
      navigation.goBack();
    }
  };

  const handleRitualStart = () => {
    setRitualStarted(true);
  };

  const handleRitualComplete = async (durationMs: number, recordingUri?: string) => {
    setLoading(true);

    try {
      const apiClient = getApiClient();

      // Prepare audio file for verification
      let verificationFile: FilePickerResult | undefined;

      if (ritualMode === 'file' && audioFile) {
        verificationFile = audioFile;
      } else if (ritualMode === 'mic' && recordingUri) {
        verificationFile = {
          uri: recordingUri,
          name: 'ritual_recording.aac',
          type: 'audio/aac',
        };
      }

      const response = await apiClient.decrypt(vaultId, ritualMode, verificationFile);

      Alert.alert(
        'Vault Unlocked!',
        `${response.message}\n\nDecrypted ${response.files.length} file(s)`,
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Ritual verification failed';
      Alert.alert('Unlock Failed', message);
      setRitualStarted(false);
      setLoading(false);
    }
  };

  const handleRitualError = (error: string) => {
    Alert.alert('Ritual Error', error);
    setRitualStarted(false);
  };

  const renderModeSelector = () => {
    if (!vault) return null;

    const fileAllowed = isRitualModeAllowed(vault.profile, 'file');
    const micAllowed = isRitualModeAllowed(vault.profile, 'mic');

    if (vault.profile === 'Black Vault') {
      return (
        <View style={styles.modeInfo}>
          <Text style={styles.modeInfoText}>
            🖤 Black Vault requires microphone ritual only
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.modeSelector}>
        <Text style={styles.modeSelectorTitle}>Ritual Mode</Text>

        <View style={styles.modeButtons}>
          <TouchableOpacity
            style={[
              styles.modeButton,
              ritualMode === 'file' && styles.modeButtonSelected,
              !fileAllowed && styles.modeButtonDisabled,
            ]}
            onPress={() => setRitualMode('file')}
            disabled={!fileAllowed}
          >
            <Text style={[
              styles.modeButtonText,
              ritualMode === 'file' && styles.modeButtonTextSelected,
            ]}>
              📁 File Upload
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.modeButton,
              ritualMode === 'mic' && styles.modeButtonSelected,
              !micAllowed && styles.modeButtonDisabled,
            ]}
            onPress={() => setRitualMode('mic')}
            disabled={!micAllowed}
          >
            <Text style={[
              styles.modeButtonText,
              ritualMode === 'mic' && styles.modeButtonTextSelected,
            ]}>
              🎤 Microphone
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (!vault) {
    return null;
  }

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
        <Text style={styles.title}>Unlock Vault</Text>
        <Text style={styles.vaultName}>{vault.name}</Text>

        <View style={styles.sigilContainer}>
          <SigilPreview
            sigilUrl={vault.sigil_url}
            runeId={vault.rune_id}
            size="lg"
          />
        </View>

        {!ritualStarted && renderModeSelector()}

        {!ritualStarted && ritualMode === 'file' && (
          <AudioSelector
            onSelect={setAudioFile}
            selectedFile={audioFile}
            showWarning={false}
          />
        )}

        {!ritualStarted && (
          <View style={styles.instructions}>
            <Text style={styles.instructionsTitle}>How to Unlock</Text>
            <Text style={styles.instructionsText}>
              {ritualMode === 'file'
                ? 'Select the same audio track you used to bind this vault. The app will play it internally and verify the timing.'
                : 'Play the ritual audio track on external speakers while this app records via microphone. The full track must be played to unlock.'}
            </Text>
          </View>
        )}

        <AudioRitualControl
          mode={ritualMode}
          audioFile={audioFile}
          onStart={handleRitualStart}
          onComplete={handleRitualComplete}
          onError={handleRitualError}
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

  vaultName: {
    ...typography.subtitle,
    color: colors.textSecondary,
    marginBottom: spacing.lg,
  },

  sigilContainer: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },

  modeSelector: {
    marginBottom: spacing.lg,
  },

  modeSelectorTitle: {
    ...typography.heading,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },

  modeButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
  },

  modeButton: {
    flex: 1,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: 8,
    padding: spacing.md,
    alignItems: 'center',
  },

  modeButtonSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primary + '20',
  },

  modeButtonDisabled: {
    opacity: 0.3,
  },

  modeButtonText: {
    ...typography.body,
    color: colors.textSecondary,
  },

  modeButtonTextSelected: {
    color: colors.primary,
    fontWeight: typography.bodyBold.fontWeight,
  },

  modeInfo: {
    backgroundColor: colors.blackVaultAccent + '20',
    borderRadius: 8,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.blackVaultAccent,
  },

  modeInfoText: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },

  instructions: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },

  instructionsTitle: {
    ...typography.heading,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },

  instructionsText: {
    ...typography.body,
    color: colors.textSecondary,
  },
});
