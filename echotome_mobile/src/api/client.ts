/**
 * Echotome Mobile v3.0 API Client
 *
 * HTTP client for communicating with Echotome v3.0 backend
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
  ErrorResponse,
  FilePickerResult,
  RitualMode,
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

  /**
   * Health check
   */
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * List all vaults
   */
  async listVaults(): Promise<Vault[]> {
    const response = await this.client.get<Vault[]>('/vaults');
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
    audioFile?: FilePickerResult
  ): Promise<DecryptResponse> {
    const formData = new FormData();
    formData.append('vault_id', vaultId);
    formData.append('ritual_mode', ritualMode);

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
