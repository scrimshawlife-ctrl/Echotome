/**
 * Echotome Mobile v3.0 FormField Component
 *
 * Text input with label and error message
 */

import React from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ViewStyle,
  TextStyle,
  TextInputProps,
} from 'react-native';
import { colors } from '../theme/colors';
import { spacing, componentSpacing } from '../theme/spacing';
import { typography } from '../theme/typography';

export interface FormFieldProps extends TextInputProps {
  label?: string;
  error?: string;
  containerStyle?: ViewStyle;
  inputStyle?: TextStyle;
  labelStyle?: TextStyle;
  errorStyle?: TextStyle;
}

export function FormField({
  label,
  error,
  containerStyle,
  inputStyle,
  labelStyle,
  errorStyle,
  ...textInputProps
}: FormFieldProps) {
  return (
    <View style={[styles.container, containerStyle]}>
      {label && <Text style={[styles.label, labelStyle]}>{label}</Text>}

      <TextInput
        style={[
          styles.input,
          error && styles.inputError,
          inputStyle,
        ]}
        placeholderTextColor={colors.textTertiary}
        {...textInputProps}
      />

      {error && <Text style={[styles.error, errorStyle]}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.md,
  },

  label: {
    ...typography.label,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },

  input: {
    ...typography.body,
    backgroundColor: colors.surface,
    color: colors.textPrimary,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: componentSpacing.inputBorderRadius,
    paddingVertical: componentSpacing.inputPaddingVertical,
    paddingHorizontal: componentSpacing.inputPaddingHorizontal,
  },

  inputError: {
    borderColor: colors.danger,
  },

  error: {
    ...typography.caption,
    color: colors.danger,
    marginTop: spacing.xs,
  },
});
