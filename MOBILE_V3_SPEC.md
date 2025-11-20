# Echotome Mobile v3.0 Specification

**Official specification for the Echotome Ritual Cryptography mobile client**

---

## Overview

A React Native mobile application (Android-first) that serves as the client interface for Echotome v3.0's Ritual Cryptography Engine.

### Purpose
- Create and manage cryptographic vaults
- Bind vaults to audio rituals (songs/tracks)
- Unlock vaults through real-time audio playback verification
- Support both file playback and microphone-based ritual verification
- Hide all cryptographic complexity behind symbolic, ritual-focused UX

---

## Architecture

### Technology Stack
- **Framework**: React Native with TypeScript
- **Navigation**: React Navigation (bottom tabs + stack)
- **API Client**: Axios
- **Audio Playback**: react-native-track-player (or equivalent)
- **Audio Recording**: react-native-audio-recorder (for microphone mode)
- **File Picker**: react-native-document-picker
- **Target Platform**: Android (primary), iOS (structure included)

### Project Structure

```
echotome_mobile/
├── package.json
├── tsconfig.json
├── babel.config.js
├── app.json
├── android/           # Android native code
├── ios/              # iOS native code (optional)
├── src/
│   ├── api/
│   │   ├── client.ts          # API client implementation
│   │   └── types.ts           # API type definitions
│   ├── components/
│   │   ├── VaultCard.tsx
│   │   ├── PrivacyPill.tsx
│   │   ├── SigilPreview.tsx
│   │   ├── AudioSelector.tsx
│   │   ├── PlaybackStatusBar.tsx
│   │   ├── AudioRitualControl.tsx
│   │   ├── FormField.tsx
│   │   └── Button.tsx
│   ├── screens/
│   │   ├── VaultListScreen.tsx
│   │   ├── CreateVaultScreen.tsx
│   │   ├── BindRitualScreen.tsx
│   │   ├── VaultDetailScreen.tsx
│   │   ├── EncryptScreen.tsx
│   │   ├── DecryptScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── navigation/
│   │   └── index.tsx
│   ├── config/
│   │   └── env.ts
│   ├── theme/
│   │   ├── colors.ts
│   │   ├── spacing.ts
│   │   └── typography.ts
│   ├── utils/
│   │   ├── validation.ts
│   │   ├── formatting.ts
│   │   └── audioHelpers.ts
│   └── App.tsx
└── README_MOBILE.md
```

---

## Backend Integration

### API Endpoints

The mobile app integrates with Echotome v3.0 backend via HTTP:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Backend health check |
| `/vaults` | GET | List all vaults |
| `/create_vault` | POST | Create new vault |
| `/bind_ritual` | POST | Bind audio track to vault (creates ROC, sigil, etc.) |
| `/encrypt` | POST | Encrypt file into vault |
| `/decrypt` | POST | Decrypt file from vault (with ritual verification) |
| `/verify_playback` | POST | Validate timing during ritual playback |

### Configuration

**Default API Base URL**: `http://10.0.2.2:8000` (Android emulator → host)

Configurable via Settings screen.

---

## Core Types

### Vault
```typescript
interface Vault {
  id: string;
  name: string;
  profile: "Quick Lock" | "Ritual Lock" | "Black Vault";
  rune_id: string;
  created_at: number;
  updated_at: number;
  has_certificate: boolean;
  sigil_url?: string;
}
```

### Requests
```typescript
interface CreateVaultRequest {
  name: string;
  profile: Vault["profile"];
}

interface BindRitualRequest {
  vault_id: string;
  profile: Vault["profile"];
  // Audio file attached as multipart
}

interface EncryptRequest {
  vault_id: string;
  file: {
    uri: string;
    name: string;
    type: string;
  };
}

interface DecryptRequest {
  vault_id: string;
  // Audio file for ritual verification
  ritual_mode: "file" | "mic";
}

interface VerifyPlaybackRequest {
  vault_id: string;
  playback_session_id: string;
  duration_ms: number;
}
```

---

## Design System

### Colors

**Base Palette**:
- `background`: #0A0A0F
- `surface`: #1A1A24
- `primary`: #6366F1
- `accent`: #8B5CF6
- `danger`: #EF4444
- `success`: #10B981

**Profile Colors**:
- **Quick Lock**: `#60A5FA` (soft blue)
- **Ritual Lock**: `#8B5CF6` (purple)
- **Black Vault**: `#1F1F1F` (deep black with subtle accent)

### Spacing
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px

### Typography
- `title`: 24px, bold
- `subtitle`: 18px, semibold
- `body`: 16px, regular
- `caption`: 14px, regular

---

## Screen Flows

### 1. Vault List → Create Vault → Bind Ritual

```
VaultListScreen
  ↓ (tap "+")
CreateVaultScreen (name + profile selection)
  ↓ (submit)
BindRitualScreen (select audio track)
  ↓ (bind ritual)
VaultDetailScreen (show bound vault with sigil)
```

### 2. Encrypt File

```
VaultDetailScreen
  ↓ (tap "Encrypt")
EncryptScreen (pick file)
  ↓ (submit)
[API: encrypt file]
  ↓ (success)
VaultDetailScreen (updated)
```

### 3. Decrypt (Ritual Unlock)

```
VaultDetailScreen
  ↓ (tap "Unlock")
DecryptScreen
  ↓ (select ritual mode: file or mic)
AudioRitualControl
  ↓ (perform ritual)
  - File mode: play audio internally
  - Mic mode: record while user plays on speakers
  ↓ (ritual complete)
[API: decrypt with ritual verification]
  ↓ (success)
Show decrypted files
```

---

## Privacy Profiles & UX Behavior

### Quick Lock 🔓
- **Audio Dependence**: None (passphrase only)
- **Timing Enforcement**: No
- **Microphone Mode**: Optional
- **UX Text**: "Fast encryption for everyday use. Audio is aesthetic only."
- **Unlock**: Allows upload-only unlock

### Ritual Lock 🔮
- **Audio Dependence**: 70%
- **Timing Enforcement**: Yes (TSC validation)
- **Microphone Mode**: Optional
- **UX Text**: "Symbolic audio binding with timing verification. Requires full track playback."
- **Unlock**: Requires full track playback (file or mic)

### Black Vault 🖤
- **Audio Dependence**: 100%
- **Timing Enforcement**: Yes (strict)
- **Microphone Mode**: **REQUIRED**
- **Deniability**: Decoy headers
- **UX Text**: "Maximum security. You must perform a microphone ritual to unlock."
- **Unlock**: ONLY microphone ritual allowed

---

## UX Principles

### No Crypto Exposure
Users never see:
- Raw hashes
- Keys
- Temporal hashes
- ROC internals
- RIV values

### Symbolic Language
All states use ritual/symbolic terminology:
- ✅ "Listening…"
- ✅ "Aligning waveform…"
- ✅ "Matching imprint…"
- ✅ "Ritual in progress…"
- ✅ "Vault unlocked"
- ❌ "Computing SHA-256…"
- ❌ "Deriving final key…"

### Error Messages
Clear, non-technical:
- ✅ "This audio doesn't match the ritual bound to this vault."
- ✅ "Playback was too short; the entire track must be played."
- ✅ "Ritual failed – timing mismatch detected."
- ❌ "Temporal hash verification failed"
- ❌ "Active region mismatch"

---

## Component Specifications

### VaultCard
**Props**: `vault: Vault`, `onPress: () => void`

Displays:
- Vault name (title)
- PrivacyPill (profile indicator)
- Rune ID (shortened, e.g., "ECH-A1B2C3D4")
- Last used timestamp (formatted, e.g., "2 hours ago")
- Touchable → navigates to VaultDetailScreen

### PrivacyPill
**Props**: `profile: Vault["profile"]`

Visual indicator:
- Rounded pill shape
- Background color based on profile
- Text label (e.g., "Quick Lock", "Ritual Lock", "Black Vault")

### SigilPreview
**Props**: `sigilUrl?: string`, `runeId: string`

Displays:
- Sigil image if available
- Fallback: abstract gradient + rune ID initials
- Square aspect ratio (1:1)

### AudioSelector
**Props**: `onSelect: (file) => void`, `selectedFile?: File`

Features:
- Document picker button
- Shows selected filename + duration
- For high-security profiles, shows warning: "You may be required to play this track via microphone later."

### PlaybackStatusBar
**Props**: `progress: number`, `status: string`, `error?: string`

Shows:
- Progress bar (0-100%)
- Status text (e.g., "Listening…", "Aligning waveform…")
- Error message if present

### AudioRitualControl
**Props**: `mode: "file" | "mic"`, `onStart`, `onComplete`, `onError`

Modes:
1. **File Mode**: Internal playback
   - Uses react-native-track-player
   - Measures real-time duration

2. **Mic Mode**: External playback + recording
   - Uses microphone recording
   - User plays track on speakers
   - App records for duration matching

Button states:
- Idle: "Start Ritual"
- Active: "Ritual in progress… (MM:SS) Tap to cancel"

---

## Screen Details

### VaultListScreen
- **Type**: FlatList of VaultCard components
- **Empty State**: "Create your first vault" with illustration
- **FAB**: "+" button → CreateVaultScreen
- **Pull to Refresh**: Reload vaults from backend

### CreateVaultScreen
- **Form Fields**:
  - Text input: Vault name
  - Profile selector: Quick / Ritual / Black (using PrivacyPill buttons)
- **Submit**: Creates vault → navigates to BindRitualScreen
- **Validation**: Non-empty name required

### BindRitualScreen
- **Context**: Shows vault name + profile
- **Explanation**: Brief description of what ritual binding means for this profile
- **AudioSelector**: Pick track
- **Profile Behavior Display**:
  - Quick Lock: "Track used as aesthetic key; upload unlock allowed"
  - Ritual Lock: "Track with timing enforcement; upload allowed"
  - Black Vault: "Microphone ritual required for unlock"
- **Submit**: "Bind Ritual" → calls `/bind_ritual` with audio file

### VaultDetailScreen
- **Header**: Vault name + PrivacyPill
- **Sigil**: SigilPreview component
- **Metadata**:
  - Rune ID
  - "Ritual bound" / "Not bound yet"
  - "Has certificate" badge
- **Actions**:
  - "Encrypt into Vault" → EncryptScreen
  - "Unlock Vault" → DecryptScreen

### EncryptScreen
- **Context**: Vault info
- **File Picker**: Select file to encrypt
- **Summary**: "File will be encrypted using your ritual key"
- **Submit**: Calls `/encrypt` → shows success/failure

### DecryptScreen
- **Context**: Vault info + SigilPreview
- **Ritual Mode Selection**:
  - Quick Lock: File or Mic (user choice)
  - Ritual Lock: File or Mic (user choice)
  - Black Vault: **Mic ONLY** (enforced in UI)
- **AudioRitualControl**: Perform ritual
- **Flow**:
  1. Select mode
  2. Start ritual
  3. Complete playback/recording
  4. Backend verification
  5. Show decrypted files or error

### SettingsScreen
- **API Base URL**: Text input + "Reset to default"
- **Preferences**: "Allow upload-only for Quick Lock" toggle
- **Debug Info**: Health status, vault count
- **Simple, non-technical wording**

---

## Android/APK Build

### Requirements
- Minimum SDK: 24
- Target SDK: 33+
- Application ID: `com.echotome.mobile`

### Build Commands

**Install dependencies**:
```bash
cd echotome_mobile
npm install
```

**Run on emulator/device**:
```bash
npx react-native run-android
```

**Build debug APK**:
```bash
cd android
./gradlew assembleDebug
```

**Output location**:
```
android/app/build/outputs/apk/debug/app-debug.apk
```

**Installation**:
- Enable "Install from unknown sources" on Android device
- Transfer APK and install
- Grant microphone and storage permissions when prompted

---

## Quality Requirements

### TypeScript
- All components typed
- No `any` types
- API responses fully typed
- Props interfaces defined

### State Management
- Explicit loading states
- Empty state handling
- Error boundary for crashes
- Graceful degradation

### No Placeholders
- All screens functional
- All navigation routes wired
- Real API integration
- No TODO comments

### Security
- No hardcoded secrets
- Backend is source of truth
- Minimal client-side validation
- All crypto handled by backend

---

## Testing Checklist

### Vault Management
- [ ] Create vault (all 3 profiles)
- [ ] List vaults
- [ ] View vault details
- [ ] Delete vault

### Ritual Binding
- [ ] Select audio file
- [ ] Upload to backend
- [ ] Receive ROC + sigil
- [ ] Display sigil

### Encryption
- [ ] Select file to encrypt
- [ ] Upload to vault
- [ ] Verify success

### Decryption (File Mode)
- [ ] Select same audio file
- [ ] Play internally
- [ ] Measure timing
- [ ] Unlock vault
- [ ] Display files

### Decryption (Mic Mode)
- [ ] Start microphone recording
- [ ] User plays track on speakers
- [ ] Record full duration
- [ ] Send to backend
- [ ] Verify timing + unlock

### Profile-Specific
- [ ] Quick Lock: Upload-only unlock works
- [ ] Ritual Lock: Timing enforcement works
- [ ] Black Vault: Mic-only enforcement works

---

## Future Enhancements (Not in v3.0)

- Offline vault browsing
- Multiple file encryption in one operation
- Vault sharing (with ROC transfer)
- Visual hash verification loop
- Biometric unlock (in addition to ritual)
- Background playback for long rituals

---

## Documentation References

- **Backend Spec**: See Echotome v3.0 backend README.md
- **API Contracts**: See backend `/docs` endpoint (FastAPI auto-docs)
- **Ritual Cryptography**: See main README.md "What is Ritual Cryptography?"

---

**Last Updated**: 2025-01-20
**Version**: 3.0.0
**Status**: Specification Complete, Implementation Pending
