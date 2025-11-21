// Echotome Web v3.1 Types

export type PrivacyProfile = 'Quick Lock' | 'Ritual Lock' | 'Black Vault';

export interface Vault {
  id: string;
  name: string;
  profile: PrivacyProfile;
  created_at: string;
  has_active_session?: boolean;
  session?: Session;
}

export interface Session {
  session_id: string;
  vault_id: string;
  profile: PrivacyProfile;
  created_at: number;
  expires_at: number;
  time_remaining: number;
  time_remaining_formatted: string;
}

export interface SessionConfig {
  profile: PrivacyProfile;
  default_ttl_seconds: number;
  max_ttl_seconds: number;
  auto_lock_on_background: boolean;
  secure_delete_on_end: boolean;
}

export interface ProfileDetail {
  name: PrivacyProfile;
  description: string;
  threat_model: string;
  session_config: SessionConfig;
}

export interface CreateVaultRequest {
  name: string;
  profile: PrivacyProfile;
  enable_recovery?: boolean;
}

export interface CreateVaultResponse {
  vault: Vault;
  message: string;
  recovery_codes?: string[];
}

export interface CreateSessionRequest {
  vault_id: string;
  profile: PrivacyProfile;
  ttl_seconds?: number;
}

export interface CreateSessionResponse {
  session: Session;
  message: string;
}

export const THREAT_MODELS: Record<PrivacyProfile, { id: string; description: string }> = {
  'Quick Lock': {
    id: 'TM-CASUAL',
    description: 'Protection against casual snooping. Not designed for adversarial threats.',
  },
  'Ritual Lock': {
    id: 'TM-TARGETED',
    description: 'Protection against targeted attacks requiring both audio ritual and passphrase.',
  },
  'Black Vault': {
    id: 'TM-COERCION',
    description: 'Deniable encryption with anti-forensic measures. Plausible deniability under duress.',
  },
};

export const SESSION_DEFAULTS: Record<PrivacyProfile, { ttl: number; maxTtl: number }> = {
  'Quick Lock': { ttl: 1800, maxTtl: 3600 },
  'Ritual Lock': { ttl: 900, maxTtl: 1800 },
  'Black Vault': { ttl: 300, maxTtl: 600 },
};
