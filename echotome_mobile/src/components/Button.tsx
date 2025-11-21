/**
 * Echotome Mobile v3.0 Button Component
 *
 * Reusable button with variants and states
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import { colors } from '../theme/colors';
import { spacing, componentSpacing, borderRadius } from '../theme/spacing';
import { typography } from '../theme/typography';

export interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  fullWidth = false,
  style,
  textStyle,
}: ButtonProps) {
  const buttonStyles: ViewStyle[] = [
    styles.base,
    styles[variant],
    styles[size],
    fullWidth && styles.fullWidth,
    (disabled || loading) && styles.disabled,
    style,
  ];

  const textStyles: TextStyle[] = [
    styles.text,
    styles[`${variant}Text` as keyof typeof styles] as TextStyle,
    styles[`${size}Text` as keyof typeof styles] as TextStyle,
    textStyle,
  ];

  return (
    <TouchableOpacity
      style={buttonStyles}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'ghost' ? colors.primary : colors.textPrimary}
          size="small"
        />
      ) : (
        <Text style={textStyles}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  // Base styles
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: componentSpacing.buttonBorderRadius,
    paddingVertical: componentSpacing.buttonPaddingVertical,
    paddingHorizontal: componentSpacing.buttonPaddingHorizontal,
  },

  // Variants
  primary: {
    backgroundColor: colors.primary,
  },

  secondary: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },

  danger: {
    backgroundColor: colors.danger,
  },

  ghost: {
    backgroundColor: colors.transparent,
  },

  // Sizes
  small: {
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
  },

  medium: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
  },

  large: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
  },

  // States
  disabled: {
    opacity: 0.5,
  },

  fullWidth: {
    width: '100%',
  },

  // Text styles
  text: {
    ...typography.button,
    color: colors.textPrimary,
    textAlign: 'center',
  },

  primaryText: {
    color: colors.textPrimary,
  },

  secondaryText: {
    color: colors.textPrimary,
  },

  dangerText: {
    color: colors.textPrimary,
  },

  ghostText: {
    color: colors.primary,
  },

  smallText: {
    ...typography.buttonSmall,
  },

  mediumText: {
    ...typography.button,
  },

  largeText: {
    ...typography.button,
    fontSize: typography.subtitle.fontSize,
  },
});
