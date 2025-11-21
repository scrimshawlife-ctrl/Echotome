/**
 * Echotome Mobile v3.0 Color Theme
 *
 * Dark, mystical aesthetic for ritual cryptography
 */

export const colors = {
  // Base palette
  background: '#0A0A0F',
  surface: '#1A1A24',
  surfaceLight: '#252532',

  // Primary colors
  primary: '#6366F1',
  primaryDark: '#4F46E5',
  primaryLight: '#818CF8',

  // Accent colors
  accent: '#8B5CF6',
  accentDark: '#7C3AED',
  accentLight: '#A78BFA',

  // Status colors
  danger: '#EF4444',
  dangerDark: '#DC2626',
  dangerLight: '#F87171',

  success: '#10B981',
  successDark: '#059669',
  successLight: '#34D399',

  warning: '#F59E0B',
  warningDark: '#D97706',
  warningLight: '#FBBF24',

  info: '#3B82F6',
  infoDark: '#2563EB',
  infoLight: '#60A5FA',

  // Text colors
  textPrimary: '#FFFFFF',
  textSecondary: '#A0A0B0',
  textTertiary: '#6B6B7B',
  textDisabled: '#4A4A54',

  // Border colors
  border: '#2A2A34',
  borderLight: '#3A3A44',
  borderFocus: '#6366F1',

  // Privacy profile colors
  quickLock: '#60A5FA',      // Soft blue
  ritualLock: '#8B5CF6',     // Purple
  blackVault: '#1F1F1F',     // Deep black
  blackVaultAccent: '#4A4A54', // Subtle accent for black vault

  // Overlay colors
  overlay: 'rgba(10, 10, 15, 0.85)',
  overlayLight: 'rgba(26, 26, 36, 0.75)',

  // Gradient colors
  gradientStart: '#6366F1',
  gradientEnd: '#8B5CF6',

  // Transparent
  transparent: 'transparent',
} as const;

export type ColorKey = keyof typeof colors;

/**
 * Get color for privacy profile
 */
export function getProfileColor(profile: 'Quick Lock' | 'Ritual Lock' | 'Black Vault'): string {
  switch (profile) {
    case 'Quick Lock':
      return colors.quickLock;
    case 'Ritual Lock':
      return colors.ritualLock;
    case 'Black Vault':
      return colors.blackVaultAccent;
    default:
      return colors.primary;
  }
}

/**
 * Get background color for privacy profile
 */
export function getProfileBackground(profile: 'Quick Lock' | 'Ritual Lock' | 'Black Vault'): string {
  switch (profile) {
    case 'Quick Lock':
      return colors.quickLock + '20'; // 20% opacity
    case 'Ritual Lock':
      return colors.ritualLock + '20';
    case 'Black Vault':
      return colors.blackVault;
    default:
      return colors.surface;
  }
}
