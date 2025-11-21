/**
 * Echotome Mobile v3.0 SigilPreview Component
 *
 * Displays sigil image with fallback gradient
 */

import React from 'react';
import { View, Image, Text, StyleSheet, ViewStyle } from 'react-native';
import { colors } from '../theme/colors';
import { sigilSizes } from '../theme/spacing';
import { typography } from '../theme/typography';
import { getInitials } from '../utils/formatting';

export interface SigilPreviewProps {
  sigilUrl?: string;
  runeId: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  style?: ViewStyle;
}

export function SigilPreview({
  sigilUrl,
  runeId,
  size = 'md',
  style,
}: SigilPreviewProps) {
  const dimensions = sigilSizes[size];

  if (sigilUrl) {
    return (
      <Image
        source={{ uri: sigilUrl }}
        style={[
          styles.sigil,
          { width: dimensions, height: dimensions },
          style,
        ]}
        resizeMode="cover"
      />
    );
  }

  // Fallback: gradient with initials
  const initials = getInitials(runeId, 3);

  return (
    <View
      style={[
        styles.fallback,
        { width: dimensions, height: dimensions },
        style,
      ]}
    >
      <Text style={[styles.initials, styles[`initials${size.toUpperCase()}` as keyof typeof styles] as any]}>
        {initials}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  sigil: {
    borderRadius: 12,
    backgroundColor: colors.surface,
  },

  fallback: {
    borderRadius: 12,
    backgroundColor: colors.gradient,
    justifyContent: 'center',
    alignItems: 'center',
    // Gradient effect (simplified)
    borderWidth: 2,
    borderColor: colors.primary,
  },

  initials: {
    ...typography.title,
    color: colors.textPrimary,
    fontWeight: typography.title.fontWeight,
  },

  initialsSM: {
    fontSize: 16,
  },

  initialsMD: {
    fontSize: 24,
  },

  initialsLG: {
    fontSize: 36,
  },

  initialsXL: {
    fontSize: 48,
  },
});
