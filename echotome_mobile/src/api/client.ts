/**
 * Echotome Mobile v3.1 API Client
 *
 * HTTP client for communicating with Echotome v3.1 backend
 * Includes session management, recovery codes, and threat model support
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  Vault,
  CreateVaultRequest,
  CreateVaultResponse,
  BindRitualResponse,
  EncryptResponse,
  DecryptResponse,
  VerifyPlaybackRequest,
  VerifyPlaybackResponse,
  HealthResponse,
  ApiInfoResponse,
  ErrorResponse,
  FilePickerResult,
  RitualMode,
  // v3.1 session types
  Session,
  CreateSessionRequest,
  CreateSessionResponse,
  ListSessionsResponse,
  ExtendSessionRequest,
  ExtendSessionResponse,
  EndSessionResponse,
  SessionConfig,
  ProfileInfo,
  ProfileDetail,
  RecoveryCodesResponse,
} from './types';

/**
 * Default API configuration
 */
const DEFAULT_BASE_URL = 'http://10.0.2.2:8000'; // Android emulator -> host
const DEFAULT_TIMEOUT = 30000; // 30 seconds

/**
 * API Client class
 */
export class EchotomeApiClient {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = DEFAULT_BASE_URL) {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: DEFAULT_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        return Promise.reject(this.handleError(error));
      }
    );
  }

  /**
   * Update base URL
   */
  setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl;
    this.client.defaults.baseURL = baseUrl;
  }

  /**
   * Get current base URL
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  // =========================================================================
  // Health & Info
  // =========================================================================

  /**
   * Health check
   */
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * API info (v3.1)
   */
  async info(): Promise<ApiInfoResponse> {
    const response = await this.client.get<ApiInfoResponse>('/info');
    return response.data;
  }

  // =========================================================================
  // Profiles (v3.1 enhanced)
  // =========================================================================

  /**
   * List all profiles with threat models
   */
  async listProfiles(): Promise<{ profiles: ProfileInfo[]; info: any }> {
    const response = await this.client.get('/profiles');
    return response.data;
  }

  /**
   * Get profile detail with threat model
   */
  async getProfile(profileName: string): Promise<ProfileDetail> {
    const response = await this.client.get<ProfileDetail>(`/profiles/${encodeURIComponent(profileName)}`);
    return response.data;
  }

  /**
   * Get session config for profile
   */
  async getProfileSessionConfig(profileName: string): Promise<SessionConfig> {
    const response = await this.client.get<SessionConfig>(`/profiles/${encodeURIComponent(profileName)}/session_config`);
    return response.data;
  }

  // =========================================================================
  // Sessions (v3.1)
  // =========================================================================

  /**
   * Create a new ritual session
   */
  async createSession(request: CreateSessionRequest): Promise<CreateSessionResponse> {
    const response = await this.client.post<CreateSessionResponse>('/sessions', request);
    return response.data;
  }

  /**
   * List all active sessions
   */
  async listSessions(): Promise<ListSessionsResponse> {
    const response = await this.client.get<ListSessionsResponse>('/sessions');
    return response.data;
  }

  /**
   * Get session by ID
   */
  async getSession(sessionId: string): Promise<Session> {
    const response = await this.client.get<Session>(`/sessions/${sessionId}`);
    return response.data;
  }

  /**
   * Extend session TTL
   */
  async extendSession(sessionId: string, additionalSeconds: number): Promise<ExtendSessionResponse> {
    const response = await this.client.post<ExtendSessionResponse>(
      `/sessions/${sessionId}/extend`,
      { additional_seconds: additionalSeconds }
    );
    return response.data;
  }

  /**
   * End session (lock vault)
   */
  async endSession(sessionId: string, secureDelete: boolean = true): Promise<EndSessionResponse> {
    const response = await this.client.delete<EndSessionResponse>(
      `/sessions/${sessionId}`,
      { params: { secure_delete: secureDelete } }
    );
    return response.data;
  }

  /**
   * Cleanup expired sessions
   */
  async cleanupSessions(): Promise<{ status: string; sessions_cleaned: number }> {
    const response = await this.client.post('/sessions/cleanup');
    return response.data;
  }

  /**
   * End all sessions (emergency lock)
   */
  async endAllSessions(secureDelete: boolean = true): Promise<{ status: string; sessions_ended: number }> {
    const response = await this.client.delete('/sessions', {
      params: { secure_delete: secureDelete }
    });
    return response.data;
  }

  // =========================================================================
  // Recovery Codes (v3.1)
  // =========================================================================

  /**
   * Generate recovery codes for a vault
   */
  async generateRecoveryCodes(vaultId: string, count: number = 5): Promise<RecoveryCodesResponse> {
    const formData = new FormData();
    formData.append('vault_id', vaultId);
    formData.append('count', count.toString());

    const response = await this.client.post<RecoveryCodesResponse>('/recovery/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // =========================================================================
  // Vaults
  // =========================================================================

  /**
   * List all vaults
   */
  async listVaults(): Promise<Vault[]> {
    const response = await this.client.get('/vaults');
    return response.data.vaults || response.data;
  }

  /**
   * Get vault by ID (includes session status in v3.1)
   */
  async getVault(vaultId: string): Promise<Vault> {
    const response = await this.client.get<Vault>(`/vaults/${vaultId}`);
    return response.data;
  }

  /**
   * Create new vault
   */
  async createVault(request: CreateVaultRequest): Promise<CreateVaultResponse> {
    const response = await this.client.post<CreateVaultResponse>('/create_vault', request);
    return response.data;
  }

  /**
   * Delete vault
   */
  async deleteVault(vaultId: string): Promise<{ status: string; vault_id: string }> {
    const response = await this.client.delete(`/vaults/${vaultId}`);
    return response.data;
  }

  /**
   * Bind ritual to vault
   */
  async bindRitual(
    vaultId: string,
    profile: string,
    audioFile: FilePickerResult
  ): Promise<BindRitualResponse> {
    const formData = new FormData();
    formData.append('vault_id', vaultId);
    formData.append('profile', profile);

    // Append audio file
    formData.append('audio', {
      uri: audioFile.uri,
      type: audioFile.type || 'audio/wav',
      name: audioFile.name,
    } as any);

    const response = await this.client.post<BindRitualResponse>('/bind_ritual', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // Longer timeout for audio processing
    });

    return response.data;
  }

  /**
   * Encrypt file into vault
   */
  async encrypt(vaultId: string, file: FilePickerResult): Promise<EncryptResponse> {
    const formData = new FormData();
    formData.append('vault_id', vaultId);
    formData.append('file', {
      uri: file.uri,
      type: file.type || 'application/octet-stream',
      name: file.name,
    } as any);

    const response = await this.client.post<EncryptResponse>('/encrypt', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });

    return response.data;
  }

  /**
   * Decrypt vault with ritual verification
   */
  async decrypt(
    vaultId: string,
    ritualMode: RitualMode,
    audioFile?: FilePickerResult,
    createSession: boolean = true
  ): Promise<DecryptResponse> {
    const formData = new FormData();
    formData.append('vault_id', vaultId);
    formData.append('ritual_mode', ritualMode);
    formData.append('create_session', createSession.toString());

    if (audioFile && ritualMode === 'file') {
      formData.append('audio', {
        uri: audioFile.uri,
        type: audioFile.type || 'audio/wav',
        name: audioFile.name,
      } as any);
    }

    const response = await this.client.post<DecryptResponse>('/decrypt', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });

    return response.data;
  }

  /**
   * Verify playback timing
   */
  async verifyPlayback(request: VerifyPlaybackRequest): Promise<VerifyPlaybackResponse> {
    const response = await this.client.post<VerifyPlaybackResponse>('/verify_playback', request);
    return response.data;
  }

  /**
   * Handle API errors
   */
  private handleError(error: AxiosError<ErrorResponse>): Error {
    if (error.response) {
      // Server responded with error
      const errorData = error.response.data;
      const message = errorData?.error || error.message;
      const detail = errorData?.detail;

      return new Error(detail ? `${message}: ${detail}` : message);
    } else if (error.request) {
      // No response received
      return new Error('Cannot reach Echotome server. Check your connection and API URL.');
    } else {
      // Request setup error
      return new Error(error.message);
    }
  }
}

/**
 * Global API client instance
 */
let apiClient: EchotomeApiClient | null = null;

/**
 * Get or create API client instance
 */
export function getApiClient(baseUrl?: string): EchotomeApiClient {
  if (!apiClient || (baseUrl && baseUrl !== apiClient.getBaseUrl())) {
    apiClient = new EchotomeApiClient(baseUrl);
  }
  return apiClient;
}

/**
 * Reset API client (for testing or configuration changes)
 */
export function resetApiClient(): void {
  apiClient = null;
}

/**
 * Export default instance
 */
export default getApiClient();
