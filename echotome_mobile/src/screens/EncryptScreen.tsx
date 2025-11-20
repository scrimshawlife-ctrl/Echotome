/**
 * Echotome Mobile v3.0 EncryptScreen
 *
 * Encrypt file into vault
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
import DocumentPicker from 'react-native-document-picker';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { Button } from '../components/Button';
import { formatFileSize } from '../utils/formatting';
import { validateEncryptFile } from '../utils/validation';
import { getApiClient } from '../api/client';
import type { FilePickerResult } from '../api/types';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type Props = NativeStackScreenProps<any, 'Encrypt'>;

export function EncryptScreen({ navigation, route }: Props) {
  const { vaultId } = route.params as { vaultId: string };

  const [file, setFile] = useState<FilePickerResult>();
  const [loading, setLoading] = useState(false);

  const handlePickFile = async () => {
    try {
      const result = await DocumentPicker.pickSingle({
        type: [DocumentPicker.types.allFiles],
        copyTo: 'cachesDirectory',
      });

      // Validate file
      const validation = validateEncryptFile(result.uri, result.size);
      if (!validation.valid) {
        Alert.alert('Invalid File', validation.error || 'Invalid file');
        return;
      }

      const pickedFile: FilePickerResult = {
        uri: result.fileCopyUri || result.uri,
        name: result.name,
        type: result.type || 'application/octet-stream',
        size: result.size,
      };

      setFile(pickedFile);
    } catch (error) {
      if (DocumentPicker.isCancel(error)) {
        return;
      }

      Alert.alert('Error', 'Failed to select file');
      console.error('File picker error:', error);
    }
  };

  const handleEncrypt = async () => {
    if (!file) {
      Alert.alert('No File Selected', 'Please select a file to encrypt');
      return;
    }

    setLoading(true);

    try {
      const apiClient = getApiClient();
      const response = await apiClient.encrypt(vaultId, file);

      Alert.alert(
        'Encryption Complete',
        response.message || 'File encrypted successfully',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to encrypt file';
      Alert.alert('Error', message);
      setLoading(false);
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
        <Text style={styles.title}>Encrypt File</Text>
        <Text style={styles.subtitle}>
          Select a file to encrypt and store securely in this vault
        </Text>

        <View style={styles.info}>
          <Text style={styles.infoTitle}>How Encryption Works</Text>
          <Text style={styles.infoText}>
            Your file will be encrypted using your vault's ritual key. The encrypted file will be
            stored securely and can only be decrypted by performing the ritual unlock.
          </Text>
        </View>

        <Button
          title={file ? 'Change File' : 'Select File'}
          onPress={handlePickFile}
          variant="secondary"
          fullWidth
        />

        {file && (
          <View style={styles.fileInfo}>
            <Text style={styles.fileName} numberOfLines={1}>
              📄 {file.name}
            </Text>
            {file.size && (
              <Text style={styles.fileSize}>{formatFileSize(file.size)}</Text>
            )}
          </View>
        )}

        <Button
          title="Encrypt into Vault"
          onPress={handleEncrypt}
          variant="primary"
          fullWidth
          loading={loading}
          disabled={loading || !file}
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

  info: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },

  infoTitle: {
    ...typography.heading,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },

  infoText: {
    ...typography.body,
    color: colors.textSecondary,
  },

  fileInfo: {
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: spacing.md,
    marginVertical: spacing.md,
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
});
