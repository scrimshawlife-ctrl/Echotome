/**
 * Echotome Mobile v3.0 App Entry Point
 *
 * Main application component
 */

import React, { useEffect } from 'react';
import { StatusBar, LogBox } from 'react-native';
import { RootNavigator } from './navigation';
import { colors } from './theme/colors';
import { initializePlayback } from './utils/audioHelpers';

// Ignore specific warnings
LogBox.ignoreLogs([
  'Non-serializable values were found in the navigation state',
]);

export default function App() {
  useEffect(() => {
    // Initialize audio playback system
    initializePlayback().catch((error) => {
      console.error('Failed to initialize audio:', error);
    });
  }, []);

  return (
    <>
      <StatusBar
        barStyle="light-content"
        backgroundColor={colors.background}
      />
      <RootNavigator />
    </>
  );
}
