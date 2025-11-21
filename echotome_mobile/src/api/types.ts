/**
 * Echotome Mobile v3.1 API Type Definitions
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
  // v3.1 additions
  has_active_session?: boolean;
  session?: SessionInfo;
}

/**
 * Session info (v3.1)
 */
export interface SessionInfo {
  session_id: string;
  time_remaining: number;
  time_remaining_formatted: string;
}

/**
 * Full session data (v3.1)
 */
export interface Session {
  session_id: string;
  vault_id: string;
  profile: PrivacyProfile;
  created_at: number;
  expires_at: number;
  time_remaining: number;
  time_remaining_formatted: string;
  last_activity?: number;
  is_expired?: boolean;
}

/**
 * Create session request (v3.1)
 */
export interface CreateSessionRequest {
  vault_id: string;
  profile: PrivacyProfile;
  ttl_seconds?: number;
}

/**
 * Create session response (v3.1)
 */
export interface CreateSessionResponse {
  session_id: string;
  vault_id: string;
  profile: PrivacyProfile;
  created_at: number;
  expires_at: number;
  time_remaining: number;
  time_remaining_formatted: string;
}

/**
 * List sessions response (v3.1)
 */
export interface ListSessionsResponse {
  sessions: Session[];
  count: number;
}

/**
 * Extend session request (v3.1)
 */
export interface ExtendSessionRequest {
  additional_seconds: number;
}

/**
 * Extend session response (v3.1)
 */
export interface ExtendSessionResponse {
  session_id: string;
  expires_at: number;
  time_remaining: number;
  time_remaining_formatted: string;
}

/**
 * End session response (v3.1)
 */
export interface EndSessionResponse {
  status: string;
  session_id: string;
  secure_delete: boolean;
}

/**
 * Session config per profile (v3.1)
 */
export interface SessionConfig {
  profile: PrivacyProfile;
  default_ttl_seconds: number;
  max_ttl_seconds: number;
  auto_lock_on_background: boolean;
  allow_external_apps: boolean;
  secure_delete: boolean;
}

/**
 * Profile with threat model (v3.1)
 */
export interface ProfileInfo {
  name: PrivacyProfile;
  kdf_time: number;
  kdf_memory: number;
  kdf_parallelism: number;
  audio_weight: number;
  deniable: boolean;
  requires_mic: boolean;
  requires_timing: boolean;
  hardware_recommended: boolean;
  threat_model_id: string;
  threat_model_description: string;
  unrecoverable_default: boolean;
}

/**
 * Profile detail with threat model (v3.1)
 */
export interface ProfileDetail {
  name: PrivacyProfile;
  threat_model: {
    id: string;
    description: string;
    assumptions: string;
    protects_against: string;
    does_not_protect_against: string;
  };
  kdf: {
    time: number;
    memory: number;
    parallelism: number;
  };
  ritual: {
    requires_mic: boolean;
    requires_timing: boolean;
    allows_visual_ritual: boolean;
  };
  recovery_enabled_default: boolean;
}

/**
 * Recovery codes response (v3.1)
 */
export interface RecoveryCodesResponse {
  vault_id: string;
  codes: string[];
  warning: string;
  count: number;
  hashes_stored: number;
}

/**
 * Create vault request
 */
export interface CreateVaultRequest {
  name: string;
  profile: PrivacyProfile;
  enable_recovery?: boolean;
}

/**
 * Create vault response
 */
export interface CreateVaultResponse {
  vault: Vault;
  message: string;
  // v3.1 additions
  vault_id?: string;
  recovery_codes?: string[];
  recovery_warning?: string;
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
  create_session?: boolean;
  // Audio file for ritual verification (if file mode)
}

/**
 * Decrypt response
 */
export interface DecryptResponse {
  vault_id: string;
  files: string[];
  message: string;
  // v3.1: session info if create_session=true
  session?: SessionInfo;
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
  timestamp?: number;
}

/**
 * API info response (v3.1)
 */
export interface ApiInfoResponse {
  name: string;
  version: string;
  edition: string;
  features: string[];
  locality: string;
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
