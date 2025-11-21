/**
 * Echotome Mobile v3.0 Spacing System
 *
 * Consistent spacing scale for layout and components
 */

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
  xxxl: 64,
} as const;

export type SpacingKey = keyof typeof spacing;

/**
 * Border radius values
 */
export const borderRadius = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
} as const;

/**
 * Component-specific spacing
 */
export const componentSpacing = {
  // Cards
  cardPadding: spacing.md,
  cardMargin: spacing.sm,
  cardBorderRadius: borderRadius.lg,

  // Buttons
  buttonPaddingVertical: spacing.sm,
  buttonPaddingHorizontal: spacing.lg,
  buttonBorderRadius: borderRadius.md,

  // Input fields
  inputPaddingVertical: spacing.sm,
  inputPaddingHorizontal: spacing.md,
  inputBorderRadius: borderRadius.md,

  // Screen padding
  screenPaddingHorizontal: spacing.md,
  screenPaddingVertical: spacing.md,

  // List items
  listItemPadding: spacing.md,
  listItemSpacing: spacing.sm,

  // Pills
  pillPaddingVertical: spacing.xs,
  pillPaddingHorizontal: spacing.sm,
  pillBorderRadius: borderRadius.full,
} as const;

/**
 * Icon sizes
 */
export const iconSizes = {
  xs: 16,
  sm: 20,
  md: 24,
  lg: 32,
  xl: 48,
  xxl: 64,
} as const;

/**
 * Avatar/sigil sizes
 */
export const sigilSizes = {
  sm: 48,
  md: 80,
  lg: 128,
  xl: 192,
} as const;
