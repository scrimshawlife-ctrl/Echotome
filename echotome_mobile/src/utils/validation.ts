/**
 * Echotome Mobile v3.0 Validation Utilities
 *
 * Input validation and error checking
 */

import { VALIDATION } from '../config/env';
import type { PrivacyProfile } from '../api/types';

/**
 * Validation result
 */
export interface ValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Validate vault name
 */
export function validateVaultName(name: string): ValidationResult {
  if (!name || name.trim().length === 0) {
    return {
      valid: false,
      error: 'Vault name cannot be empty',
    };
  }

  if (name.length < VALIDATION.VAULT_NAME_MIN_LENGTH) {
    return {
      valid: false,
      error: `Vault name must be at least ${VALIDATION.VAULT_NAME_MIN_LENGTH} character`,
    };
  }

  if (name.length > VALIDATION.VAULT_NAME_MAX_LENGTH) {
    return {
      valid: false,
      error: `Vault name must be less than ${VALIDATION.VAULT_NAME_MAX_LENGTH} characters`,
    };
  }

  return { valid: true };
}

/**
 * Validate privacy profile
 */
export function validatePrivacyProfile(profile: string): ValidationResult {
  const validProfiles: PrivacyProfile[] = ['Quick Lock', 'Ritual Lock', 'Black Vault'];

  if (!validProfiles.includes(profile as PrivacyProfile)) {
    return {
      valid: false,
      error: 'Invalid privacy profile',
    };
  }

  return { valid: true };
}

/**
 * Validate audio file
 */
export function validateAudioFile(
  uri: string,
  size?: number,
  duration?: number
): ValidationResult {
  if (!uri) {
    return {
      valid: false,
      error: 'No audio file selected',
    };
  }

  // Check file size
  if (size && size > VALIDATION.MAX_AUDIO_FILE_SIZE) {
    const maxMB = Math.round(VALIDATION.MAX_AUDIO_FILE_SIZE / 1024 / 1024);
    return {
      valid: false,
      error: `Audio file is too large (max ${maxMB}MB)`,
    };
  }

  // Check duration
  if (duration) {
    if (duration < VALIDATION.MIN_AUDIO_DURATION) {
      return {
        valid: false,
        error: `Audio must be at least ${VALIDATION.MIN_AUDIO_DURATION} seconds`,
      };
    }

    if (duration > VALIDATION.MAX_AUDIO_DURATION) {
      const maxMin = Math.round(VALIDATION.MAX_AUDIO_DURATION / 60);
      return {
        valid: false,
        error: `Audio must be less than ${maxMin} minutes`,
      };
    }
  }

  return { valid: true };
}

/**
 * Validate file for encryption
 */
export function validateEncryptFile(uri: string, size?: number): ValidationResult {
  if (!uri) {
    return {
      valid: false,
      error: 'No file selected',
    };
  }

  // Check file size
  if (size && size > VALIDATION.MAX_ENCRYPT_FILE_SIZE) {
    const maxMB = Math.round(VALIDATION.MAX_ENCRYPT_FILE_SIZE / 1024 / 1024);
    return {
      valid: false,
      error: `File is too large (max ${maxMB}MB)`,
    };
  }

  return { valid: true };
}

/**
 * Validate API URL
 */
export function validateApiUrl(url: string): ValidationResult {
  if (!url || url.trim().length === 0) {
    return {
      valid: false,
      error: 'API URL cannot be empty',
    };
  }

  // Basic URL validation
  try {
    const urlObj = new URL(url);
    if (!['http:', 'https:'].includes(urlObj.protocol)) {
      return {
        valid: false,
        error: 'API URL must use HTTP or HTTPS',
      };
    }
  } catch (error) {
    return {
      valid: false,
      error: 'Invalid URL format',
    };
  }

  return { valid: true };
}

/**
 * Validate rune ID format
 */
export function validateRuneId(runeId: string): ValidationResult {
  if (!runeId) {
    return {
      valid: false,
      error: 'Rune ID cannot be empty',
    };
  }

  // Expected format: ECH-XXXXXXXX
  const runePattern = /^ECH-[A-Z0-9]{8}$/;
  if (!runePattern.test(runeId)) {
    return {
      valid: false,
      error: 'Invalid rune ID format',
    };
  }

  return { valid: true };
}

/**
 * Check if ritual mode is allowed for profile
 */
export function isRitualModeAllowed(
  profile: PrivacyProfile,
  mode: 'file' | 'mic'
): boolean {
  if (profile === 'Black Vault') {
    // Black Vault requires microphone only
    return mode === 'mic';
  }

  // Quick Lock and Ritual Lock allow both modes
  return true;
}

/**
 * Get ritual mode requirements for profile
 */
export function getRitualModeRequirements(profile: PrivacyProfile): string {
  switch (profile) {
    case 'Quick Lock':
      return 'File or microphone (optional)';
    case 'Ritual Lock':
      return 'File or microphone (required for unlock)';
    case 'Black Vault':
      return 'Microphone only (strictly required)';
    default:
      return 'Unknown';
  }
}
