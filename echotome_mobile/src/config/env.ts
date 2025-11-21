/**
 * Echotome Mobile v3.0 Environment Configuration
 *
 * Configuration constants and environment variables
 */

/**
 * API configuration
 */
export const API_CONFIG = {
  // Default API base URL (Android emulator -> host machine)
  DEFAULT_BASE_URL: 'http://10.0.2.2:8000',

  // Alternative URLs for different environments
  LOCALHOST: 'http://localhost:8000',
  DEVICE_IP: 'http://192.168.1.100:8000', // Replace with actual device IP

  // Timeouts
  DEFAULT_TIMEOUT: 30000,    // 30 seconds
  UPLOAD_TIMEOUT: 60000,     // 60 seconds for file uploads
  RITUAL_TIMEOUT: 120000,    // 2 minutes for ritual verification
} as const;

/**
 * Audio configuration
 */
export const AUDIO_CONFIG = {
  // Sample rate for audio processing
  SAMPLE_RATE: 16000,

  // Audio format
  ENCODING: 'wav',
  CHANNELS: 1, // Mono

  // Playback timing tolerance (80-120% speed)
  MIN_SPEED_TOLERANCE: 0.8,
  MAX_SPEED_TOLERANCE: 1.2,

  // Recording settings
  BITRATE: 128000,
  QUALITY: 'high',
} as const;

/**
 * UI configuration
 */
export const UI_CONFIG = {
  // Animation durations
  ANIMATION_SHORT: 200,
  ANIMATION_MEDIUM: 300,
  ANIMATION_LONG: 500,

  // Refresh intervals
  VAULT_REFRESH_INTERVAL: 5000, // 5 seconds

  // Debounce delays
  SEARCH_DEBOUNCE: 300,
  INPUT_DEBOUNCE: 500,
} as const;

/**
 * Storage keys for AsyncStorage
 */
export const STORAGE_KEYS = {
  API_BASE_URL: '@echotome:api_base_url',
  DEVICE_ID: '@echotome:device_id',
  SETTINGS: '@echotome:settings',
  LAST_VAULT_ID: '@echotome:last_vault_id',
} as const;

/**
 * Privacy profile configuration
 */
export const PROFILE_CONFIG = {
  QUICK_LOCK: {
    name: 'Quick Lock',
    emoji: '🔓',
    audioDependence: 0,
    timingEnforcement: false,
    microphoneRequired: false,
    description: 'Fast encryption for everyday use. Audio is aesthetic only.',
  },
  RITUAL_LOCK: {
    name: 'Ritual Lock',
    emoji: '🔮',
    audioDependence: 0.7,
    timingEnforcement: true,
    microphoneRequired: false,
    description: 'Symbolic audio binding with timing verification. Requires full track playback.',
  },
  BLACK_VAULT: {
    name: 'Black Vault',
    emoji: '🖤',
    audioDependence: 1.0,
    timingEnforcement: true,
    microphoneRequired: true,
    description: 'Maximum security. You must perform a microphone ritual to unlock.',
  },
} as const;

/**
 * Validation rules
 */
export const VALIDATION = {
  // Vault name
  VAULT_NAME_MIN_LENGTH: 1,
  VAULT_NAME_MAX_LENGTH: 100,

  // File size limits
  MAX_AUDIO_FILE_SIZE: 100 * 1024 * 1024, // 100 MB
  MAX_ENCRYPT_FILE_SIZE: 500 * 1024 * 1024, // 500 MB

  // Audio duration
  MIN_AUDIO_DURATION: 10, // 10 seconds
  MAX_AUDIO_DURATION: 3600, // 1 hour
} as const;

/**
 * Feature flags
 */
export const FEATURES = {
  // Enable debug logging
  DEBUG: __DEV__,

  // Enable offline mode
  OFFLINE_MODE: false,

  // Enable biometric unlock
  BIOMETRIC_UNLOCK: false,
} as const;
