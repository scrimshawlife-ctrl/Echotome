# Echotome v3.2 Client Integration Guide

**For**: Mobile & Web Developers
**Version**: 3.2.0
**API**: Session & Locality Enforcement

## Table of Contents

1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Session Workflow](#session-workflow)
4. [Client Implementation](#client-implementation)
5. [Security Best Practices](#security-best-practices)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Overview

### v3.2 Key Changes

**Session-Based Access**:
- Decrypt now creates time-limited sessions
- Files accessible via session endpoints
- Automatic cleanup on expiration

**Profile-Based TTLs**:
- Quick Lock: 1 hour
- Ritual Lock: 20 minutes
- Black Vault: 5 minutes

**Enhanced Security**:
- Locality enforcement (local-only operations)
- Path traversal protection
- Secure deletion support

---

## API Endpoints

### Base URL

```
http://localhost:8000  # Development
https://api.echotome.example.com  # Production
```

### Core Endpoints

#### 1. API Information

```http
GET /info
```

**Response**:
```json
{
  "name": "Echotome",
  "version": "3.2.0",
  "edition": "Session & Locality Enforcement",
  "features": [
    "time_limited_sessions",
    "profile_based_ttls",
    "locality_enforcement"
  ]
}
```

#### 2. List Profiles

```http
GET /profiles
```

**Response**:
```json
{
  "profiles": [
    {
      "name": "Quick Lock",
      "session_ttl_seconds": 3600,
      "session_ttl_formatted": "60 minutes",
      "allow_plaintext_disk": true,
      "threat_model_id": "casual",
      "kdf_time": 2,
      "kdf_memory": 65536
    }
  ]
}
```

#### 3. Encrypt File

```http
POST /encrypt
Content-Type: multipart/form-data
```

**Parameters**:
- `audio_file` (file): Audio for AF-KDF
- `passphrase` (string): User passphrase
- `profile` (string): "Quick Lock" | "Ritual Lock" | "Black Vault"
- `data_file` (file): File to encrypt

**Response**:
```json
{
  "rune_id": "abc123...",
  "profile": "Ritual Lock",
  "encrypted_blob": "{...json blob...}"
}
```

#### 4. Decrypt File (v3.2)

```http
POST /decrypt
Content-Type: multipart/form-data
```

**Parameters**:
- `audio_file` (file): Audio for AF-KDF
- `passphrase` (string): User passphrase
- `encrypted_blob` (string): JSON encrypted blob
- `create_session` (boolean): `true` (default) | `false`
- `vault_id` (string, optional): Vault identifier

**Response** (when `create_session=true`):
```json
{
  "status": "decrypted",
  "session_created": true,
  "session": {
    "session_id": "abc123-def456-...",
    "vault_id": "my-vault",
    "profile": "Ritual Lock",
    "created_at": 1700000000.0,
    "expires_at": 1700001200.0,
    "time_remaining_seconds": 1200,
    "time_remaining_formatted": "20:00"
  },
  "file": {
    "filename": "decrypted_file",
    "access_url": "/sessions/abc123.../files/decrypted_file"
  }
}
```

#### 5. List Sessions

```http
GET /sessions
```

**Response**:
```json
{
  "sessions": [
    {
      "session_id": "abc123...",
      "vault_id": "my-vault",
      "profile": "Ritual Lock",
      "time_remaining": 1180,
      "is_expired": false
    }
  ],
  "count": 1
}
```

#### 6. Get Session Details

```http
GET /sessions/{session_id}
```

**Response**:
```json
{
  "session_id": "abc123...",
  "vault_id": "my-vault",
  "profile": "Ritual Lock",
  "created_at": 1700000000.0,
  "expires_at": 1700001200.0,
  "time_remaining": 1180,
  "time_remaining_formatted": "19:40"
}
```

#### 7. List Session Files (v3.2)

```http
GET /sessions/{session_id}/files
```

**Response**:
```json
{
  "session_id": "abc123...",
  "vault_id": "my-vault",
  "profile": "Ritual Lock",
  "time_remaining": 1180,
  "files": [
    {
      "filename": "document.pdf",
      "size_bytes": 1024000,
      "download_url": "/sessions/abc123.../files/document.pdf"
    }
  ],
  "file_count": 1
}
```

#### 8. Download Session File (v3.2)

```http
GET /sessions/{session_id}/files/{filename}
```

**Response**: Binary file download

#### 9. Extend Session

```http
POST /sessions/{session_id}/extend
Content-Type: application/json
```

**Body**:
```json
{
  "additional_seconds": 600
}
```

**Response**:
```json
{
  "session_id": "abc123...",
  "expires_at": 1700001800.0,
  "time_remaining": 1780
}
```

#### 10. End Session (Lock)

```http
DELETE /sessions/{session_id}?secure_delete=true
```

**Response**:
```json
{
  "status": "ended",
  "session_id": "abc123...",
  "secure_delete": true
}
```

#### 11. Emergency Lock (End All)

```http
DELETE /sessions?secure_delete=true
```

**Response**:
```json
{
  "status": "all_sessions_ended",
  "sessions_ended": 3,
  "secure_delete": true
}
```

---

## Session Workflow

### Typical Flow

```
1. User selects profile → GET /profiles (show TTLs)
2. User uploads audio + file → POST /encrypt → Store encrypted_blob
3. User wants to decrypt → POST /decrypt → Receive session_id
4. App displays session timer → Use time_remaining
5. User accesses files → GET /sessions/{id}/files → List available
6. User downloads file → GET /sessions/{id}/files/{name}
7. Session expires OR user locks → DELETE /sessions/{id}
8. Background cleanup → Plaintext wiped automatically
```

### Session Lifecycle

```
┌─────────┐
│ DECRYPT │ → Session Created (profile-based TTL)
└─────────┘
     │
     v
┌─────────────┐
│   ACTIVE    │ → Files accessible via /sessions/{id}/files
└─────────────┘
     │
     ├─→ User activity → Session remains active
     │
     ├─→ TTL expires → Auto-lock, secure delete
     │
     └─→ User locks → Manual lock, secure delete
          │
          v
     ┌─────────┐
     │ EXPIRED │ → Files no longer accessible (404)
     └─────────┘
```

---

## Client Implementation

### React Native (Mobile)

**SessionManager.ts**:

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

interface Session {
  session_id: string;
  vault_id: string;
  profile: string;
  expires_at: number;
  time_remaining: number;
}

class EchotomeSessionManager {
  private apiBase = 'http://localhost:8000';
  private sessionTimers: Map<string, NodeJS.Timeout> = new Map();

  async decrypt(
    audioFile: File,
    passphrase: string,
    encryptedBlob: string
  ): Promise<Session> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('passphrase', passphrase);
    formData.append('encrypted_blob', encryptedBlob);
    formData.append('create_session', 'true');

    const response = await fetch(`${this.apiBase}/decrypt`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Decrypt failed: ${response.statusText}`);
    }

    const data = await response.json();
    const session = data.session;

    // Store session
    await AsyncStorage.setItem(`session_${session.session_id}`, JSON.stringify(session));

    // Start countdown timer
    this.startSessionTimer(session);

    return session;
  }

  startSessionTimer(session: Session): void {
    const timer = setInterval(async () => {
      // Update time remaining
      const timeLeft = Math.max(0, session.expires_at - Date.now() / 1000);

      if (timeLeft === 0) {
        // Session expired
        clearInterval(timer);
        this.sessionTimers.delete(session.session_id);
        await this.handleExpiration(session.session_id);
      }

      // Emit event for UI update
      this.emit('sessionUpdate', { session_id: session.session_id, time_remaining: timeLeft });
    }, 1000);

    this.sessionTimers.set(session.session_id, timer);
  }

  async listSessionFiles(sessionId: string): Promise<any[]> {
    const response = await fetch(`${this.apiBase}/sessions/${sessionId}/files`);

    if (response.status === 404) {
      throw new Error('Session expired or not found');
    }

    const data = await response.json();
    return data.files;
  }

  async downloadFile(sessionId: string, filename: string): Promise<Blob> {
    const response = await fetch(
      `${this.apiBase}/sessions/${sessionId}/files/${filename}`
    );

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    return await response.blob();
  }

  async lockSession(sessionId: string, secureDelete: boolean = true): Promise<void> {
    await fetch(`${this.apiBase}/sessions/${sessionId}?secure_delete=${secureDelete}`, {
      method: 'DELETE',
    });

    // Clear timer
    const timer = this.sessionTimers.get(sessionId);
    if (timer) {
      clearInterval(timer);
      this.sessionTimers.delete(sessionId);
    }

    // Remove from storage
    await AsyncStorage.removeItem(`session_${sessionId}`);
  }

  async emergencyLock(): Promise<number> {
    const response = await fetch(`${this.apiBase}/sessions?secure_delete=true`, {
      method: 'DELETE',
    });

    const data = await response.json();

    // Clear all timers
    this.sessionTimers.forEach(timer => clearInterval(timer));
    this.sessionTimers.clear();

    // Clear storage
    const keys = await AsyncStorage.getAllKeys();
    const sessionKeys = keys.filter(k => k.startsWith('session_'));
    await AsyncStorage.multiRemove(sessionKeys);

    return data.sessions_ended;
  }

  private async handleExpiration(sessionId: string): Promise<void> {
    // Emit expiration event
    this.emit('sessionExpired', { session_id: sessionId });

    // Clean up storage
    await AsyncStorage.removeItem(`session_${sessionId}`);
  }

  // Event emitter methods (simplified)
  private listeners: Map<string, Function[]> = new Map();

  on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  private emit(event: string, data: any): void {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(cb => cb(data));
  }
}

export default new EchotomeSessionManager();
```

**Usage in Component**:

```tsx
import React, { useState, useEffect } from 'react';
import { View, Text, Button, FlatList } from 'react-native';
import SessionManager from './SessionManager';

export function VaultScreen() {
  const [session, setSession] = useState(null);
  const [files, setFiles] = useState([]);
  const [timeRemaining, setTimeRemaining] = useState(0);

  useEffect(() => {
    // Listen for session updates
    SessionManager.on('sessionUpdate', ({ session_id, time_remaining }) => {
      if (session && session_id === session.session_id) {
        setTimeRemaining(time_remaining);
      }
    });

    SessionManager.on('sessionExpired', ({ session_id }) => {
      if (session && session_id === session.session_id) {
        alert('Session expired! Vault locked.');
        setSession(null);
        setFiles([]);
      }
    });
  }, [session]);

  const handleDecrypt = async () => {
    try {
      const newSession = await SessionManager.decrypt(audioFile, passphrase, encryptedBlob);
      setSession(newSession);
      setTimeRemaining(newSession.time_remaining);

      // Load files
      const sessionFiles = await SessionManager.listSessionFiles(newSession.session_id);
      setFiles(sessionFiles);
    } catch (error) {
      alert(`Decrypt failed: ${error.message}`);
    }
  };

  const handleLock = async () => {
    if (session) {
      await SessionManager.lockSession(session.session_id);
      setSession(null);
      setFiles([]);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <View>
      {session ? (
        <>
          <Text>Session Active: {session.profile}</Text>
          <Text>Time Remaining: {formatTime(timeRemaining)}</Text>
          <Button title="Lock Vault" onPress={handleLock} />

          <FlatList
            data={files}
            keyExtractor={item => item.filename}
            renderItem={({ item }) => (
              <View>
                <Text>{item.filename} ({(item.size_bytes / 1024).toFixed(2)} KB)</Text>
                <Button
                  title="Download"
                  onPress={() => SessionManager.downloadFile(session.session_id, item.filename)}
                />
              </View>
            )}
          />
        </>
      ) : (
        <Button title="Unlock Vault" onPress={handleDecrypt} />
      )}
    </View>
  );
}
```

### Next.js (Web)

**hooks/useEchotomeSession.ts**:

```typescript
import { useState, useEffect, useCallback } from 'react';

interface Session {
  session_id: string;
  profile: string;
  time_remaining: number;
  expires_at: number;
}

export function useEchotomeSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(0);

  // Countdown timer
  useEffect(() => {
    if (!session) return;

    const interval = setInterval(() => {
      const remaining = Math.max(0, session.expires_at - Date.now() / 1000);
      setTimeRemaining(remaining);

      if (remaining === 0) {
        // Session expired
        setSession(null);
        alert('Session expired! Vault locked.');
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [session]);

  const decrypt = useCallback(async (audioFile: File, passphrase: string, encryptedBlob: string) => {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('passphrase', passphrase);
    formData.append('encrypted_blob', encryptedBlob);
    formData.append('create_session', 'true');

    const response = await fetch('/api/decrypt', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Decrypt failed');
    }

    const data = await response.json();
    setSession(data.session);
    setTimeRemaining(data.session.time_remaining_seconds);

    return data;
  }, []);

  const lock = useCallback(async () => {
    if (!session) return;

    await fetch(`/api/sessions/${session.session_id}`, {
      method: 'DELETE',
    });

    setSession(null);
    setTimeRemaining(0);
  }, [session]);

  return { session, timeRemaining, decrypt, lock };
}
```

---

## Security Best Practices

### 1. Never Store Passphrases

```typescript
// ❌ BAD
await AsyncStorage.setItem('passphrase', passphrase);

// ✅ GOOD
// Prompt user each time, never persist
```

### 2. Clear Sensitive Data on Background

```typescript
// React Native
import { AppState } from 'react-native';

AppState.addEventListener('change', async (state) => {
  if (state === 'background') {
    // Lock sessions for Black Vault profile
    if (session.profile === 'Black Vault') {
      await SessionManager.lockSession(session.session_id);
    }
  }
});
```

### 3. Handle Session Expiration Gracefully

```typescript
// Always check for 404 errors
try {
  const files = await listSessionFiles(sessionId);
} catch (error) {
  if (error.status === 404) {
    // Session expired - handle gracefully
    showExpirationWarning();
    clearLocalState();
  }
}
```

### 4. Secure Delete by Default

```typescript
// Always use secure delete for sensitive data
await lockSession(sessionId, true);  // secure_delete=true
```

### 5. Locality Awareness

```typescript
// v3.2: All operations are local-only
// No need for CORS configuration
// No external network calls
// API must be on same machine as crypto operations
```

---

## Error Handling

### Common Error Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Invalid request (bad audio/passphrase) | Show user-friendly error |
| 404 | Session not found/expired | Clear local state, prompt re-auth |
| 403 | Path traversal attempt blocked | Log security event |
| 500 | Server error | Retry with exponential backoff |

### Example Error Handler

```typescript
async function handleApiError(error: Response): Promise<string> {
  switch (error.status) {
    case 400:
      return 'Invalid audio file or passphrase. Please try again.';
    case 404:
      return 'Session expired. Please unlock the vault again.';
    case 403:
      return 'Access denied.';
    case 500:
      return 'Server error. Please try again later.';
    default:
      return 'An unexpected error occurred.';
  }
}
```

---

## Examples

### Complete Encrypt/Decrypt Cycle

```typescript
// 1. Encrypt
const encryptResult = await fetch('/api/encrypt', {
  method: 'POST',
  body: formData,
});
const { encrypted_blob, rune_id } = await encryptResult.json();

// Store encrypted_blob (safe to persist)
await storage.setItem(`vault_${rune_id}`, encrypted_blob);

// 2. Decrypt (creates session)
const decryptResult = await fetch('/api/decrypt', {
  method: 'POST',
  body: decryptFormData,
});
const { session, file } = await decryptResult.json();

// 3. Access files
const filesResult = await fetch(`/api/sessions/${session.session_id}/files`);
const { files } = await filesResult.json();

// 4. Download specific file
const fileBlob = await fetch(files[0].download_url);
const data = await fileBlob.blob();

// 5. Lock when done
await fetch(`/api/sessions/${session.session_id}`, { method: 'DELETE' });
```

### Profile Selection UI

```typescript
const profiles = await fetch('/api/profiles').then(r => r.json());

profiles.profiles.forEach(profile => {
  console.log(`${profile.name}: ${profile.session_ttl_formatted}`);
  console.log(`Threat Model: ${profile.threat_model_id}`);
  console.log(`KDF Time: ~${profile.kdf_time * 5}s`);  // Approximate
  console.log('---');
});

// Let user choose based on:
// - Session duration needs
// - Security level required
// - Acceptable KDF wait time
```

---

## Migration from v3.1

### Breaking Changes

1. **Decrypt response changed**:
   ```typescript
   // v3.1: Direct file download
   const file = await response.blob();

   // v3.2: Session + file URL
   const { session, file } = await response.json();
   const blob = await fetch(file.access_url).then(r => r.blob());
   ```

2. **Session TTLs are profile-dependent** (was configurable per request)

3. **New endpoints**: `/sessions/{id}/files` and `/sessions/{id}/files/{filename}`

### Backward Compatibility

Use `create_session=false` for legacy mode:

```typescript
// v3.1-style direct download
const formData = new FormData();
formData.append('create_session', 'false');  // Opt out of sessions

const response = await fetch('/api/decrypt', {
  method: 'POST',
  body: formData,
});

const fileBlob = await response.blob();  // Direct download (legacy)
```

---

## Support

- **API Documentation**: `/docs` (Swagger/OpenAPI)
- **Issues**: GitHub Issues
- **Examples**: `echotome/examples/` directory

---

**End of Client Integration Guide**
