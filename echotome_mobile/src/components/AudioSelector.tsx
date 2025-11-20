/**
 * Echotome Mobile v3.0 AudioSelector Component
 *
 * File picker for selecting audio files
 */

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import DocumentPicker from 'react-native-document-picker';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { formatFileSize, formatDuration } from '../utils/formatting';
import { validateAudioFile } from '../utils/validation';
import { isValidAudioFile } from '../utils/audioHelpers';
import { Button } from './Button';
import type { FilePickerResult } from '../api/types';

export interface AudioSelectorProps {
  onSelect: (file: FilePickerResult) => void;
  selectedFile?: FilePickerResult;
  showWarning?: boolean;
  warningText?: string;
}

export function AudioSelector({
  onSelect,
  selectedFile,
  showWarning = false,
  warningText = 'You may be required to play this track via microphone later.',
}: AudioSelectorProps) {
  const handlePickAudio = async () => {
    try {
      const result = await DocumentPicker.pickSingle({
        type: [DocumentPicker.types.audio],
        copyTo: 'cachesDirectory',
      });

      // Validate file name
      if (!isValidAudioFile(result.name)) {
        Alert.alert('Invalid File', 'Please select a valid audio file (WAV, MP3, M4A, AAC, OGG, FLAC)');
        return;
      }

      // Validate file size and duration
      const validation = validateAudioFile(result.uri, result.size);
      if (!validation.valid) {
        Alert.alert('Invalid File', validation.error || 'Invalid audio file');
        return;
      }

      const file: FilePickerResult = {
        uri: result.fileCopyUri || result.uri,
        name: result.name,
        type: result.type || 'audio/wav',
        size: result.size,
      };

      onSelect(file);
    } catch (error) {
      if (DocumentPicker.isCancel(error)) {
        // User cancelled the picker
        return;
      }

      Alert.alert('Error', 'Failed to select audio file');
      console.error('Audio picker error:', error);
    }
  };

  return (
    <View style={styles.container}>
      <Button
        title={selectedFile ? 'Change Audio Track' : 'Select Audio Track'}
        onPress={handlePickAudio}
        variant="secondary"
        fullWidth
      />

      {selectedFile && (
        <View style={styles.fileInfo}>
          <Text style={styles.fileName} numberOfLines={1}>
            🎵 {selectedFile.name}
          </Text>
          {selectedFile.size && (
            <Text style={styles.fileSize}>
              {formatFileSize(selectedFile.size)}
            </Text>
          )}
        </View>
      )}

      {showWarning && (
        <View style={styles.warning}>
          <Text style={styles.warningIcon}>⚠️</Text>
          <Text style={styles.warningText}>{warningText}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.md,
  },

  fileInfo: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: spacing.md,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },

  fileName: {
    ...typography.body,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },

  fileSize: {
    ...typography.caption,
    color: colors.textSecondary,
  },

  warning: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.warningDark + '20',
    borderRadius: 8,
    padding: spacing.sm,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.warning + '40',
  },

  warningIcon: {
    fontSize: 16,
    marginRight: spacing.xs,
  },

  warningText: {
    ...typography.caption,
    color: colors.warning,
    flex: 1,
  },
});
