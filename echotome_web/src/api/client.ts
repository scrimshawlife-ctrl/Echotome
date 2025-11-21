// Echotome Web v3.1 API Client

import axios, { AxiosInstance } from 'axios';
import type {
  Vault,
  Session,
  CreateVaultRequest,
  CreateVaultResponse,
  CreateSessionRequest,
  CreateSessionResponse,
  ProfileDetail,
} from './types';

class EchotomeClient {
  private client: AxiosInstance;

  constructor(baseURL = '/api') {
    this.client = axios.create({ baseURL });
  }

  // Vaults
  async listVaults(): Promise<Vault[]> {
    const res = await this.client.get<{ vaults: Vault[] }>('/vaults');
    return res.data.vaults;
  }

  async getVault(id: string): Promise<Vault> {
    const res = await this.client.get<Vault>(`/vaults/${id}`);
    return res.data;
  }

  async createVault(request: CreateVaultRequest): Promise<CreateVaultResponse> {
    const res = await this.client.post<CreateVaultResponse>('/vaults', request);
    return res.data;
  }

  async deleteVault(id: string): Promise<void> {
    await this.client.delete(`/vaults/${id}`);
  }

  // Sessions
  async createSession(request: CreateSessionRequest): Promise<CreateSessionResponse> {
    const res = await this.client.post<CreateSessionResponse>('/sessions', request);
    return res.data;
  }

  async listSessions(): Promise<Session[]> {
    const res = await this.client.get<{ sessions: Session[] }>('/sessions');
    return res.data.sessions;
  }

  async getSession(id: string): Promise<Session> {
    const res = await this.client.get<Session>(`/sessions/${id}`);
    return res.data;
  }

  async extendSession(id: string, additionalSeconds: number): Promise<Session> {
    const res = await this.client.post<Session>(`/sessions/${id}/extend`, {
      additional_seconds: additionalSeconds,
    });
    return res.data;
  }

  async endSession(id: string, secureDelete = true): Promise<void> {
    await this.client.delete(`/sessions/${id}`, { params: { secure_delete: secureDelete } });
  }

  async endAllSessions(): Promise<{ count: number }> {
    const res = await this.client.post<{ count: number }>('/sessions/cleanup');
    return res.data;
  }

  // Profiles
  async getProfile(name: string): Promise<ProfileDetail> {
    const res = await this.client.get<ProfileDetail>(`/profiles/${encodeURIComponent(name)}`);
    return res.data;
  }

  // Recovery
  async generateRecoveryCodes(vaultId: string, count = 8): Promise<string[]> {
    const res = await this.client.post<{ codes: string[] }>('/recovery/generate', {
      vault_id: vaultId,
      count,
    });
    return res.data.codes;
  }
}

export const apiClient = new EchotomeClient();
export default apiClient;
