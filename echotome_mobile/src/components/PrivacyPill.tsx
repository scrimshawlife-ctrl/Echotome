/**
 * Echotome Mobile v3.0 PrivacyPill Component
 *
 * Visual indicator for privacy profile
 */

import React from 'react';
import { View, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { getProfileColor, getProfileBackground } from '../theme/colors';
import { componentSpacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import type { PrivacyProfile } from '../api/types';

export interface PrivacyPillProps {
  profile: PrivacyProfile;
  size?: 'small' | 'medium' | 'large';
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export function PrivacyPill({
  profile,
  size = 'medium',
  style,
  textStyle,
}: PrivacyPillProps) {
  const backgroundColor = getProfileBackground(profile);
  const borderColor = getProfileColor(profile);

  return (
    <View
      style={[
        styles.container,
        { backgroundColor, borderColor },
        styles[size],
        style,
      ]}
    >
      <Text style={[styles.text, styles[`${size}Text` as keyof typeof styles] as TextStyle, textStyle]}>
        {getProfileEmoji(profile)} {profile}
      </Text>
    </View>
  );
}

function getProfileEmoji(profile: PrivacyProfile): string {
  switch (profile) {
    case 'Quick Lock':
      return '🔓';
    case 'Ritual Lock':
      return '🔮';
    case 'Black Vault':
      return '🖤';
    default:
      return '🔒';
  }
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: componentSpacing.pillBorderRadius,
    borderWidth: 1,
    paddingVertical: componentSpacing.pillPaddingVertical,
    paddingHorizontal: componentSpacing.pillPaddingHorizontal,
  },

  // Sizes
  small: {
    paddingVertical: 2,
    paddingHorizontal: 6,
  },

  medium: {
    paddingVertical: componentSpacing.pillPaddingVertical,
    paddingHorizontal: componentSpacing.pillPaddingHorizontal,
  },

  large: {
    paddingVertical: 6,
    paddingHorizontal: 12,
  },

  // Text styles
  text: {
    ...typography.caption,
    fontWeight: typography.captionBold.fontWeight,
  },

  smallText: {
    fontSize: 10,
  },

  mediumText: {
    fontSize: typography.caption.fontSize,
  },

  largeText: {
    fontSize: typography.body.fontSize,
  },
});
