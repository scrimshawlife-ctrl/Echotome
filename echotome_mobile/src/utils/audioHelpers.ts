/**
 * Echotome Mobile v3.0 Audio Helpers
 *
 * Audio playback and recording utilities
 */

import TrackPlayer, { State, Event } from 'react-native-track-player';
import AudioRecorderPlayer from 'react-native-audio-recorder-player';
import { AUDIO_CONFIG } from '../config/env';
import type { PlaybackStatus, RecordingStatus, FilePickerResult } from '../api/types';

/**
 * Audio recorder player instance
 */
let recorderPlayer: AudioRecorderPlayer | null = null;

/**
 * Get or create recorder player instance
 */
function getRecorderPlayer(): AudioRecorderPlayer {
  if (!recorderPlayer) {
    recorderPlayer = new AudioRecorderPlayer();
  }
  return recorderPlayer;
}

/**
 * Initialize audio playback system
 */
export async function initializePlayback(): Promise<void> {
  try {
    await TrackPlayer.setupPlayer({
      maxCacheSize: 1024 * 10, // 10 MB
    });

    await TrackPlayer.updateOptions({
      stopWithApp: true,
      capabilities: [
        TrackPlayer.CAPABILITY_PLAY,
        TrackPlayer.CAPABILITY_PAUSE,
        TrackPlayer.CAPABILITY_STOP,
        TrackPlayer.CAPABILITY_SEEK_TO,
      ],
      compactCapabilities: [
        TrackPlayer.CAPABILITY_PLAY,
        TrackPlayer.CAPABILITY_PAUSE,
      ],
    });
  } catch (error) {
    console.error('Error initializing playback:', error);
  }
}

/**
 * Load audio file for playback
 */
export async function loadAudioFile(file: FilePickerResult): Promise<void> {
  await TrackPlayer.reset();
  await TrackPlayer.add({
    id: file.uri,
    url: file.uri,
    title: file.name,
    artist: 'Ritual Audio',
  });
}

/**
 * Start audio playback
 */
export async function startPlayback(): Promise<void> {
  await TrackPlayer.play();
}

/**
 * Pause audio playback
 */
export async function pausePlayback(): Promise<void> {
  await TrackPlayer.pause();
}

/**
 * Stop audio playback
 */
export async function stopPlayback(): Promise<void> {
  await TrackPlayer.stop();
  await TrackPlayer.reset();
}

/**
 * Get current playback position
 */
export async function getPlaybackPosition(): Promise<number> {
  return await TrackPlayer.getPosition();
}

/**
 * Get audio duration
 */
export async function getAudioDuration(): Promise<number> {
  return await TrackPlayer.getDuration();
}

/**
 * Get playback state
 */
export async function getPlaybackState(): Promise<State> {
  return await TrackPlayer.getState();
}

/**
 * Get full playback status
 */
export async function getPlaybackStatus(): Promise<PlaybackStatus> {
  const position = await getPlaybackPosition();
  const duration = await getAudioDuration();
  const state = await getPlaybackState();

  return {
    isPlaying: state === State.Playing,
    position: position * 1000, // Convert to ms
    duration: duration * 1000,
  };
}

/**
 * Seek to position in audio
 */
export async function seekTo(positionMs: number): Promise<void> {
  await TrackPlayer.seekTo(positionMs / 1000);
}

/**
 * Start audio recording
 */
export async function startRecording(outputPath: string): Promise<void> {
  const recorder = getRecorderPlayer();

  const audioSet = {
    AudioEncoderAndroid: AudioRecorderPlayer.AudioEncoderAndroidType.AAC,
    AudioSourceAndroid: AudioRecorderPlayer.AudioSourceAndroidType.MIC,
    AVEncoderAudioQualityKeyIOS: AudioRecorderPlayer.AVEncoderAudioQualityIOSType.high,
    AVNumberOfChannelsKeyIOS: AUDIO_CONFIG.CHANNELS,
    AVFormatIDKeyIOS: AudioRecorderPlayer.AVEncodingOption.aac,
  };

  await recorder.startRecorder(outputPath, audioSet);
}

/**
 * Stop audio recording
 */
export async function stopRecording(): Promise<string> {
  const recorder = getRecorderPlayer();
  const result = await recorder.stopRecorder();
  return result;
}

/**
 * Pause audio recording
 */
export async function pauseRecording(): Promise<void> {
  const recorder = getRecorderPlayer();
  await recorder.pauseRecorder();
}

/**
 * Resume audio recording
 */
export async function resumeRecording(): Promise<void> {
  const recorder = getRecorderPlayer();
  await recorder.resumeRecorder();
}

/**
 * Get recording status
 */
export function getRecordingStatus(recorder: AudioRecorderPlayer): RecordingStatus {
  // Note: react-native-audio-recorder-player provides status via callbacks
  // This is a placeholder for the interface
  return {
    isRecording: false,
    duration: 0,
  };
}

/**
 * Calculate recording duration
 */
export function calculateRecordingDuration(startTime: number): number {
  return Date.now() - startTime;
}

/**
 * Validate playback timing
 */
export function validatePlaybackTiming(
  actualDuration: number,
  expectedDuration: number
): boolean {
  const minDuration = expectedDuration * AUDIO_CONFIG.MIN_SPEED_TOLERANCE;
  const maxDuration = expectedDuration * AUDIO_CONFIG.MAX_SPEED_TOLERANCE;

  return actualDuration >= minDuration && actualDuration <= maxDuration;
}

/**
 * Get audio file info
 */
export async function getAudioFileInfo(uri: string): Promise<{ duration: number }> {
  // Load the file temporarily to get duration
  await TrackPlayer.reset();
  await TrackPlayer.add({
    id: uri,
    url: uri,
    title: 'temp',
  });

  const duration = await TrackPlayer.getDuration();
  await TrackPlayer.reset();

  return { duration: duration * 1000 }; // Convert to ms
}

/**
 * Format recording time
 */
export function formatRecordingTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Check if audio file is valid
 */
export function isValidAudioFile(filename: string): boolean {
  const validExtensions = ['.wav', '.mp3', '.m4a', '.aac', '.ogg', '.flac'];
  const ext = filename.toLowerCase().substring(filename.lastIndexOf('.'));
  return validExtensions.includes(ext);
}

/**
 * Generate output filename for recording
 */
export function generateRecordingFilename(): string {
  const timestamp = Date.now();
  return `echotome_ritual_${timestamp}.aac`;
}

/**
 * Cleanup audio resources
 */
export async function cleanupAudioResources(): Promise<void> {
  try {
    await stopPlayback();
    if (recorderPlayer) {
      await recorderPlayer.stopRecorder();
      recorderPlayer = null;
    }
  } catch (error) {
    console.error('Error cleaning up audio resources:', error);
  }
}
