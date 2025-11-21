/**
 * Echotome Mobile v3.0 AudioRitualControl Component
 *
 * Controls for performing audio ritual (file playback or microphone recording)
 */

import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { Button } from './Button';
import { PlaybackStatusBar } from './PlaybackStatusBar';
import {
  initializePlayback,
  loadAudioFile,
  startPlayback,
  stopPlayback,
  getPlaybackStatus,
  startRecording,
  stopRecording,
  generateRecordingFilename,
  formatRecordingTime,
} from '../utils/audioHelpers';
import RNFS from 'react-native-fs';
import type { FilePickerResult, RitualMode } from '../api/types';

export interface AudioRitualControlProps {
  mode: RitualMode;
  audioFile?: FilePickerResult;
  onStart: () => void;
  onComplete: (durationMs: number, recordingUri?: string) => void;
  onError: (error: string) => void;
}

export function AudioRitualControl({
  mode,
  audioFile,
  onStart,
  onComplete,
  onError,
}: AudioRitualControlProps) {
  const [isActive, setIsActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Ready to begin ritual');
  const [error, setError] = useState<string>();
  const [elapsedMs, setElapsedMs] = useState(0);

  const startTimeRef = useRef<number>(0);
  const recordingPathRef = useRef<string>('');
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      stopPlayback();
    };
  }, []);

  const handleStart = async () => {
    try {
      setIsActive(true);
      setProgress(0);
      setError(undefined);
      setElapsedMs(0);
      startTimeRef.current = Date.now();
      onStart();

      if (mode === 'file') {
        await startFileRitual();
      } else {
        await startMicRitual();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start ritual';
      setError(message);
      setIsActive(false);
      onError(message);
    }
  };

  const startFileRitual = async () => {
    if (!audioFile) {
      throw new Error('No audio file selected');
    }

    setStatus('Listening…');

    // Initialize playback
    await initializePlayback();
    await loadAudioFile(audioFile);
    await startPlayback();

    // Monitor playback progress
    intervalRef.current = setInterval(async () => {
      const playbackStatus = await getPlaybackStatus();
      const progressPercent = (playbackStatus.position / playbackStatus.duration) * 100;

      setProgress(progressPercent);
      setElapsedMs(playbackStatus.position);

      if (progressPercent < 30) {
        setStatus('Listening…');
      } else if (progressPercent < 70) {
        setStatus('Aligning waveform…');
      } else {
        setStatus('Matching imprint…');
      }

      // Check if completed
      if (progressPercent >= 99) {
        handleComplete();
      }
    }, 100);
  };

  const startMicRitual = async () => {
    setStatus('Recording ritual… Play your track on speakers');

    // Start recording
    const filename = generateRecordingFilename();
    const path = `${RNFS.CachesDirectoryPath}/${filename}`;
    recordingPathRef.current = path;

    await startRecording(path);

    // Monitor recording time
    intervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTimeRef.current;
      setElapsedMs(elapsed);
      setStatus(`Recording ritual… ${formatRecordingTime(elapsed)}`);

      // Update progress (estimate based on 3-minute max)
      const estimatedProgress = Math.min((elapsed / (3 * 60 * 1000)) * 100, 99);
      setProgress(estimatedProgress);
    }, 100);
  };

  const handleStop = async () => {
    try {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      if (mode === 'file') {
        await stopPlayback();
      } else {
        await stopRecording();
      }

      const duration = Date.now() - startTimeRef.current;
      setIsActive(false);
      setProgress(0);
      setStatus('Ritual cancelled');

      Alert.alert('Ritual Cancelled', 'The ritual was stopped before completion.');
    } catch (err) {
      console.error('Error stopping ritual:', err);
    }
  };

  const handleComplete = async () => {
    try {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      if (mode === 'file') {
        await stopPlayback();
      } else {
        await stopRecording();
      }

      const duration = Date.now() - startTimeRef.current;
      setIsActive(false);
      setProgress(100);
      setStatus('Ritual complete! Verifying…');

      onComplete(duration, mode === 'mic' ? recordingPathRef.current : undefined);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to complete ritual';
      setError(message);
      setIsActive(false);
      onError(message);
    }
  };

  return (
    <View style={styles.container}>
      {isActive && (
        <PlaybackStatusBar
          progress={progress}
          status={status}
          error={error}
        />
      )}

      {!isActive ? (
        <Button
          title="Start Ritual"
          onPress={handleStart}
          variant="primary"
          fullWidth
          disabled={mode === 'file' && !audioFile}
        />
      ) : (
        <>
          <View style={styles.activeIndicator}>
            <Text style={styles.activeText}>
              ✨ Ritual in progress… ({formatRecordingTime(elapsedMs)})
            </Text>
          </View>

          <Button
            title={mode === 'mic' ? 'Complete Ritual' : 'Cancel'}
            onPress={mode === 'mic' ? handleComplete : handleStop}
            variant={mode === 'mic' ? 'primary' : 'danger'}
            fullWidth
          />
        </>
      )}

      {mode === 'mic' && (
        <View style={styles.micHint}>
          <Text style={styles.micHintText}>
            📱 Play your ritual track on external speakers while this app records
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: spacing.md,
  },

  activeIndicator: {
    backgroundColor: colors.primary + '20',
    borderRadius: 8,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.primary + '40',
  },

  activeText: {
    ...typography.body,
    color: colors.primary,
    textAlign: 'center',
  },

  micHint: {
    backgroundColor: colors.info + '20',
    borderRadius: 8,
    padding: spacing.sm,
    marginTop: spacing.sm,
    borderWidth: 1,
    borderColor: colors.info + '40',
  },

  micHintText: {
    ...typography.caption,
    color: colors.info,
    textAlign: 'center',
  },
});
