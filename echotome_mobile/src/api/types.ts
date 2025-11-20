/**
 * Echotome Mobile v3.0 API Type Definitions
 *
 * TypeScript interfaces for API requests and responses
 */

/**
 * Privacy profiles
 */
export type PrivacyProfile = 'Quick Lock' | 'Ritual Lock' | 'Black Vault';

/**
 * Ritual modes
 */
export type RitualMode = 'file' | 'mic';

/**
 * Vault data structure
 */
export interface Vault {
  id: string;
  name: string;
  profile: PrivacyProfile;
  rune_id: string;
  created_at: number;
  updated_at: number;
  has_certificate: boolean;
  sigil_url?: string;
  encrypted_files?: string[];
}

/**
 * Create vault request
 */
export interface CreateVaultRequest {
  name: string;
  profile: PrivacyProfile;
}

/**
 * Create vault response
 */
export interface CreateVaultResponse {
  vault: Vault;
  message: string;
}

/**
 * Bind ritual request (multipart form data)
 */
export interface BindRitualRequest {
  vault_id: string;
  profile: PrivacyProfile;
  // Audio file will be sent as multipart/form-data
}

/**
 * Bind ritual response
 */
export interface BindRitualResponse {
  vault: Vault;
  roc_path: string;
  sigil_url: string;
  message: string;
}

/**
 * Encrypt request
 */
export interface EncryptRequest {
  vault_id: string;
  // File will be sent as multipart/form-data
}

/**
 * Encrypt response
 */
export interface EncryptResponse {
  vault_id: string;
  encrypted_path: string;
  message: string;
}

/**
 * Decrypt request
 */
export interface DecryptRequest {
  vault_id: string;
  ritual_mode: RitualMode;
  // Audio file for ritual verification (if file mode)
}

/**
 * Decrypt response
 */
export interface DecryptResponse {
  vault_id: string;
  files: string[];
  message: string;
}

/**
 * Verify playback request
 */
export interface VerifyPlaybackRequest {
  vault_id: string;
  playback_session_id: string;
  duration_ms: number;
}

/**
 * Verify playback response
 */
export interface VerifyPlaybackResponse {
  valid: boolean;
  message: string;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
  version: string;
  timestamp: number;
}

/**
 * Error response
 */
export interface ErrorResponse {
  error: string;
  detail?: string;
  status_code?: number;
}

/**
 * File picker result
 */
export interface FilePickerResult {
  uri: string;
  name: string;
  type: string;
  size?: number;
}

/**
 * Audio file metadata
 */
export interface AudioFileMetadata {
  uri: string;
  name: string;
  duration?: number;
  size?: number;
}

/**
 * Playback status
 */
export interface PlaybackStatus {
  isPlaying: boolean;
  position: number;
  duration: number;
  buffered?: number;
}

/**
 * Recording status
 */
export interface RecordingStatus {
  isRecording: boolean;
  duration: number;
  uri?: string;
}

/**
 * Ritual verification result
 */
export interface RitualVerificationResult {
  success: boolean;
  message: string;
  duration_ms?: number;
  error?: string;
}
