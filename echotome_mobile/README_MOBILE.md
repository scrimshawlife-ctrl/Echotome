# Echotome Mobile v3.0

**React Native mobile client for Echotome Ritual Cryptography Engine**

---

## Overview

Echotome Mobile is an Android-first mobile application that serves as the client interface for Echotome v3.0's Ritual Cryptography Engine. It allows users to:

- Create and manage cryptographic vaults
- Bind vaults to audio rituals (songs/tracks)
- Unlock vaults through real-time audio playback verification
- Support both file playback and microphone-based ritual verification
- Encrypt and decrypt files with ritual-bound keys

---

## Features

### 🔮 Privacy Profiles

- **Quick Lock** 🔓: Fast encryption, passphrase-only (audio aesthetic)
- **Ritual Lock** 🔮: 70% audio binding with timing verification
- **Black Vault** 🖤: 100% audio dependence, microphone-only unlock

### 🎵 Ritual Binding

- Upload audio tracks to bind with vaults
- Real-time playback verification
- Microphone recording for maximum security
- Timing enforcement prevents acceleration attacks

### 🔒 Vault Management

- Create vaults with symbolic names
- View vault details with sigil visualization
- Encrypt files into vaults
- Unlock vaults through ritual performance

---

## Requirements

### Development Environment

- Node.js >= 18.x
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, optional)

### Android

- Android SDK 24+
- Target SDK 33+
- Java JDK 17+

---

## Installation

### 1. Install Dependencies

```bash
cd echotome_mobile
npm install
```

### 2. iOS Setup (Optional)

```bash
cd ios
pod install
cd ..
```

### 3. Android Setup

Ensure Android SDK is installed and `ANDROID_HOME` environment variable is set:

```bash
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

---

## Running the App

### Start Metro Bundler

```bash
npm start
```

### Run on Android Emulator/Device

```bash
npm run android
```

Or:

```bash
npx react-native run-android
```

### Run on iOS Simulator (macOS only)

```bash
npm run ios
```

---

## Building APK

### Debug APK

```bash
cd android
./gradlew assembleDebug
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk`

### Release APK (Signed)

1. Generate a keystore:

```bash
keytool -genkeypair -v -storetype PKCS12 -keystore my-release-key.keystore \
  -alias my-key-alias -keyalg RSA -keysize 2048 -validity 10000
```

2. Edit `android/gradle.properties`:

```properties
MYAPP_RELEASE_STORE_FILE=my-release-key.keystore
MYAPP_RELEASE_KEY_ALIAS=my-key-alias
MYAPP_RELEASE_STORE_PASSWORD=*****
MYAPP_RELEASE_KEY_PASSWORD=*****
```

3. Build release APK:

```bash
cd android
./gradlew assembleRelease
```

Output: `android/app/build/outputs/apk/release/app-release.apk`

---

## Installation on Device

### Enable Unknown Sources

1. Go to Settings → Security
2. Enable "Install unknown apps" for your file manager

### Install APK

1. Transfer APK to device
2. Open APK file on device
3. Grant permissions when prompted:
   - Microphone (for ritual recording)
   - Storage (for file encryption/decryption)

---

## Configuration

### Backend API URL

By default, the app connects to:

- **Android Emulator**: `http://10.0.2.2:8000` (host machine)
- **Physical Device**: Update in Settings screen to your PC's IP address

### Change API URL

1. Open Echotome Mobile
2. Navigate to **Settings** tab
3. Update "API Base URL" field
4. Tap **Save**
5. Verify connection status

Example URLs:
- Emulator: `http://10.0.2.2:8000`
- Localhost: `http://localhost:8000`
- Network device: `http://192.168.1.100:8000`

---

## Project Structure

```
echotome_mobile/
├── src/
│   ├── api/                    # API client and types
│   │   ├── client.ts
│   │   └── types.ts
│   ├── components/             # Reusable UI components
│   │   ├── AudioRitualControl.tsx
│   │   ├── AudioSelector.tsx
│   │   ├── Button.tsx
│   │   ├── FormField.tsx
│   │   ├── PlaybackStatusBar.tsx
│   │   ├── PrivacyPill.tsx
│   │   ├── SigilPreview.tsx
│   │   └── VaultCard.tsx
│   ├── screens/                # App screens
│   │   ├── BindRitualScreen.tsx
│   │   ├── CreateVaultScreen.tsx
│   │   ├── DecryptScreen.tsx
│   │   ├── EncryptScreen.tsx
│   │   ├── SettingsScreen.tsx
│   │   ├── VaultDetailScreen.tsx
│   │   └── VaultListScreen.tsx
│   ├── navigation/             # React Navigation setup
│   │   └── index.tsx
│   ├── theme/                  # Design system
│   │   ├── colors.ts
│   │   ├── spacing.ts
│   │   └── typography.ts
│   ├── utils/                  # Helper functions
│   │   ├── audioHelpers.ts
│   │   ├── formatting.ts
│   │   └── validation.ts
│   ├── config/                 # App configuration
│   │   └── env.ts
│   └── App.tsx                 # Root component
├── android/                    # Android native code
├── ios/                        # iOS native code (optional)
├── package.json
├── tsconfig.json
└── babel.config.js
```

---

## Usage Workflows

### 1. Create a Vault

1. Tap **+** button on Vaults screen
2. Enter vault name
3. Select privacy profile (Quick Lock / Ritual Lock / Black Vault)
4. Tap **Create Vault**

### 2. Bind Ritual to Vault

1. Select audio track (WAV, MP3, M4A, etc.)
2. Upload to backend
3. Backend generates Ritual Ownership Certificate (ROC) and sigil
4. Vault is now bound to the audio ritual

### 3. Encrypt File

1. Open vault details
2. Tap **Encrypt into Vault**
3. Select file to encrypt
4. File is encrypted using ritual key

### 4. Unlock Vault (Decrypt)

#### File Mode (Quick Lock / Ritual Lock)
1. Open vault details
2. Tap **Unlock Vault**
3. Select same audio file
4. App plays internally and verifies timing
5. Files decrypted on success

#### Microphone Mode (Black Vault / Ritual Lock)
1. Open vault details
2. Tap **Unlock Vault**
3. Select **Microphone** mode
4. Play ritual track on speakers
5. App records via microphone
6. Backend verifies timing and audio match
7. Files decrypted on success

---

## Troubleshooting

### Cannot Connect to Backend

- Verify backend is running: `curl http://10.0.2.2:8000/health`
- Update API URL in Settings
- Check firewall settings
- Use device IP address instead of localhost

### Audio Not Playing

- Grant microphone permissions
- Check device volume
- Verify audio file format (WAV, MP3, M4A supported)

### Build Errors

- Clean build: `cd android && ./gradlew clean`
- Clear Metro cache: `npm start -- --reset-cache`
- Reinstall dependencies: `rm -rf node_modules && npm install`

### App Crashes

- Check Metro bundler logs
- Run: `npx react-native log-android` (Android)
- Run: `npx react-native log-ios` (iOS)

---

## Development

### Type Checking

```bash
npx tsc --noEmit
```

### Linting

```bash
npm run lint
```

### Format Code

```bash
npx prettier --write "src/**/*.{ts,tsx}"
```

---

## Privacy & Security

### Permissions

- **Microphone**: Required for Black Vault microphone ritual mode
- **Storage**: Required for file encryption/decryption

### Data Storage

- API URL stored in AsyncStorage
- No encryption keys stored on device
- All crypto operations handled by backend

### Network Security

- API client uses HTTPS when available
- No sensitive data transmitted without encryption
- Backend validates all ritual verification requests

---

## Known Limitations

- Android-first (iOS support requires additional testing)
- Audio playback timing validation requires trusted clock
- Large files (>500MB) may cause memory issues
- Background playback not yet supported

---

## Future Enhancements

- Offline vault browsing
- Multiple file encryption in one operation
- Vault sharing with ROC transfer
- Visual hash verification loop
- Biometric unlock (in addition to ritual)
- Background playback for long rituals

---

## Documentation

- **Backend Spec**: See main Echotome v3.0 README.md
- **Mobile Spec**: See MOBILE_V3_SPEC.md
- **API Contracts**: See backend `/docs` endpoint (FastAPI auto-docs)

---

## License

See LICENSE file in root directory.

---

## Support

For issues, questions, or contributions:
- GitHub: [scrimshawlife-ctrl/Echotome](https://github.com/scrimshawlife-ctrl/Echotome)

---

**Echotome Mobile v3.0** — Where ritual meets cryptography, in the palm of your hand.

*"The ritual is the key."*
