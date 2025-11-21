/**
 * RecoveryCodesModal Component (v3.1)
 *
 * Displays recovery codes after vault creation.
 * Warns user to save codes securely - they won't be shown again.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  Share,
  Alert,
} from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';

interface RecoveryCodesModalProps {
  visible: boolean;
  codes: string[];
  vaultName: string;
  onDismiss: () => void;
}

export const RecoveryCodesModal: React.FC<RecoveryCodesModalProps> = ({
  visible,
  codes,
  vaultName,
  onDismiss,
}) => {
  const [confirmed, setConfirmed] = useState(false);

  const handleCopy = () => {
    const text = codes.join('\n');
    Clipboard.setString(text);
    Alert.alert('Copied', 'Recovery codes copied to clipboard');
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Echotome Recovery Codes for "${vaultName}":\n\n${codes.map((c, i) => `${i + 1}. ${c}`).join('\n')}\n\nStore these securely. Each code can only be used once.`,
      });
    } catch (error) {
      // User cancelled
    }
  };

  const handleDismiss = () => {
    if (!confirmed) {
      Alert.alert(
        'Are you sure?',
        'These codes will NOT be shown again. Make sure you have saved them.',
        [
          { text: 'Go Back', style: 'cancel' },
          {
            text: 'I Saved Them',
            onPress: () => {
              setConfirmed(true);
              onDismiss();
            },
          },
        ]
      );
    } else {
      onDismiss();
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={handleDismiss}
    >
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.header}>
            <Text style={styles.title}>Recovery Codes</Text>
            <Text style={styles.subtitle}>For vault: {vaultName}</Text>
          </View>

          <View style={styles.warning}>
            <Text style={styles.warningTitle}>Save These Codes Now</Text>
            <Text style={styles.warningText}>
              These codes will NOT be shown again. Each code can only be used once
              to recover your vault if you lose access to your ritual.
            </Text>
          </View>

          <ScrollView style={styles.codesContainer}>
            {codes.map((code, index) => (
              <View key={code} style={styles.codeRow}>
                <Text style={styles.codeIndex}>{index + 1}.</Text>
                <Text style={styles.code}>{code}</Text>
              </View>
            ))}
          </ScrollView>

          <View style={styles.actions}>
            <TouchableOpacity style={styles.copyButton} onPress={handleCopy}>
              <Text style={styles.copyButtonText}>Copy All</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.shareButton} onPress={handleShare}>
              <Text style={styles.shareButtonText}>Share</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity style={styles.dismissButton} onPress={handleDismiss}>
            <Text style={styles.dismissButtonText}>I've Saved My Codes</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'center',
    padding: spacing.md,
  },
  container: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: spacing.lg,
    maxHeight: '85%',
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.textPrimary,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  warning: {
    backgroundColor: colors.warningBackground || '#4a3f00',
    borderRadius: 8,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  warningTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.warning,
    marginBottom: spacing.xs,
  },
  warningText: {
    fontSize: 13,
    color: colors.warning,
    lineHeight: 18,
  },
  codesContainer: {
    maxHeight: 250,
    marginBottom: spacing.md,
  },
  codeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  codeIndex: {
    width: 30,
    fontSize: 14,
    color: colors.textSecondary,
  },
  code: {
    flex: 1,
    fontSize: 16,
    fontFamily: 'monospace',
    color: colors.textPrimary,
    letterSpacing: 1,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  copyButton: {
    flex: 1,
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    alignItems: 'center',
  },
  copyButtonText: {
    color: colors.background,
    fontSize: 14,
    fontWeight: '600',
  },
  shareButton: {
    flex: 1,
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.primary,
    paddingVertical: spacing.sm,
    borderRadius: 8,
    alignItems: 'center',
  },
  shareButtonText: {
    color: colors.primary,
    fontSize: 14,
    fontWeight: '600',
  },
  dismissButton: {
    backgroundColor: colors.success,
    paddingVertical: spacing.md,
    borderRadius: 8,
    alignItems: 'center',
  },
  dismissButtonText: {
    color: colors.background,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default RecoveryCodesModal;
