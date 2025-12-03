import './styles.css';
import { devtoolsOpen } from './guard';

type Ui = {
  audioUpload: HTMLInputElement;
  analyzeBtn: HTMLButtonElement;
  renderKeySongBtn: HTMLButtonElement;
  exportMidiBtn: HTMLButtonElement;
  exportStems: HTMLInputElement;
  songStyle: HTMLSelectElement;
  seedMotif: HTMLInputElement;
  scalePreset: HTMLSelectElement;
  customScale: HTMLInputElement;
  medley: HTMLInputElement;
  medleyList: HTMLInputElement;
  keySongAudio: HTMLAudioElement;
  messages: HTMLDivElement;
};

const SAMPLE_RATE = 44_100;
const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const tempoByStyle: Record<string, number> = {
  ambient: 76,
  piano: 92,
  chiptune: 120,
  bass: 108,
  percussive: 126,
  modal: 98,
  trance: 134,
  lofi: 86,
};

function parseStyles(raw: string): string[] {
  return raw
    .split(/[\s,]+/)
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .filter((style) => tempoByStyle[style]);
}

const scalePresets: Record<string, number[]> = {
  ionian: [0, 2, 4, 5, 7, 9, 11],
  aeolian: [0, 2, 3, 5, 7, 8, 10],
  dorian: [0, 2, 3, 5, 7, 9, 10],
  pentatonic: [0, 3, 5, 7, 10],
};

let currentHash: string | null = null;
let currentNotes: string[] = [];

function $(id: keyof Ui): Ui[keyof Ui] {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el as Ui[keyof Ui];
}

const ui: Ui = {
  audioUpload: $('#audioUpload') as HTMLInputElement,
  analyzeBtn: $('#analyzeBtn') as HTMLButtonElement,
  renderKeySongBtn: $('#renderKeySongBtn') as HTMLButtonElement,
  exportMidiBtn: $('#exportMidiBtn') as HTMLButtonElement,
  exportStems: $('#exportStems') as HTMLInputElement,
  songStyle: $('#songStyle') as HTMLSelectElement,
  seedMotif: $('#seedMotif') as HTMLInputElement,
  scalePreset: $('#scalePreset') as HTMLSelectElement,
  customScale: $('#customScale') as HTMLInputElement,
  medley: $('#medley') as HTMLInputElement,
  medleyList: $('#medleyList') as HTMLInputElement,
  keySongAudio: $('#keySongAudio') as HTMLAudioElement,
  messages: $('#messages') as HTMLDivElement,
};

function setMessage(text: string, level: 'info' | 'warn' | 'error' = 'info') {
  const color = level === 'info' ? '#9ad5ff' : level === 'warn' ? '#ffd166' : '#ff6b6b';
  ui.messages.textContent = text;
  ui.messages.style.color = color;
}

async function hashFile(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function parseCustomScale(raw: string): number[] {
  return raw
    .split(/[\s,]+/)
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .map((chunk) => Number.parseInt(chunk, 10))
    .filter((n) => Number.isFinite(n) && n >= 0 && n <= 11);
}

function resolveScale(): number[] {
  const preset = ui.scalePreset.value;
  if (preset === 'custom') {
    const custom = parseCustomScale(ui.customScale.value);
    if (custom.length) return custom;
  }
  return scalePresets[preset] ?? scalePresets.ionian;
}

function noteFromMidi(midi: number): string {
  const octave = Math.floor(midi / 12) - 1;
  return `${noteNames[midi % 12]}${octave}`;
}

function noteToMidi(note: string): number {
  const match = note.match(/^([A-G])(#?)(-?\d+)$/i);
  if (!match) throw new Error(`Invalid note: ${note}`);
  const [, letter, sharp, octaveStr] = match;
  const baseIndex = noteNames.findIndex((n) => n.startsWith(letter.toUpperCase()));
  const pitchClass = baseIndex + (sharp ? 1 : 0);
  const octave = Number.parseInt(octaveStr, 10);
  return pitchClass + (octave + 1) * 12;
}

function transpose(note: string, semitones: number): string {
  return noteFromMidi(noteToMidi(note) + semitones);
}

function deriveNotes(hash: string, motif: string): string[] {
  const pairs = hash.match(/.{1,2}/g) ?? [];
  const scale = resolveScale();
  const motifBias = motif
    .split('')
    .map((c) => c.charCodeAt(0))
    .reduce((acc, val) => acc + val, 0);
  const root = (Number.parseInt(hash.slice(0, 2), 16) + motifBias) % 12;

  return pairs.slice(0, 32).map((pair, idx) => {
    const value = Number.parseInt(pair, 16);
    const octave = 3 + (value % 3);
    const degree = scale[value % scale.length];
    const lift = idx % 8 === 0 ? 12 : 0;
    return noteFromMidi(12 * octave + ((root + degree) % 12) + lift);
  });
}

function buildStems(notes: string[]): { lead: string[]; harmony: string[] } {
  const lead = notes.filter((_, idx) => idx % 2 === 0);
  const harmony = notes
    .filter((_, idx) => idx % 2 === 1)
    .map((note, idx) => transpose(note, idx % 3 === 0 ? -12 : 12));

  if (!harmony.length) harmony.push(...lead.map((note, idx) => transpose(note, idx % 2 === 0 ? 12 : -12)));

  return { lead, harmony };
}

function midiToFrequency(midi: number): number {
  return 440 * Math.pow(2, (midi - 69) / 12);
}

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i += 1) view.setUint8(offset + i, str.charCodeAt(i));
  };

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }

  return new Blob([buffer], { type: 'audio/wav' });
}

function synthesizeWave(notes: string[], bpm: number): Float32Array {
  const secondsPerBeat = 60 / bpm;
  const noteDuration = secondsPerBeat * 0.5; // eighth note pulse
  const totalSamples = Math.max(1, Math.ceil(notes.length * noteDuration * SAMPLE_RATE));
  const data = new Float32Array(totalSamples);

  let cursor = 0;
  const attack = 0.01 * SAMPLE_RATE;
  const release = 0.06 * SAMPLE_RATE;

  notes.forEach((note) => {
    const midi = noteToMidi(note);
    const freq = midiToFrequency(midi);
    const samplesForNote = Math.min(Math.floor(noteDuration * SAMPLE_RATE), totalSamples - cursor);
    for (let i = 0; i < samplesForNote; i += 1) {
      const envAttack = Math.min(1, i / attack);
      const envRelease = Math.min(1, (samplesForNote - i) / release);
      const envelope = Math.min(envAttack, envRelease);
      data[cursor + i] += Math.sin((2 * Math.PI * freq * i) / SAMPLE_RATE) * 0.42 * envelope;
    }
    cursor += samplesForNote;
  });

  return data;
}

function renderWave(notes: string[], bpm: number): Blob {
  return encodeWav(synthesizeWave(notes, bpm), SAMPLE_RATE);
}

function renderMedleyWave(notes: string[], styles: string[]): Blob {
  const segments = styles.map((style) => {
    const bpm = tempoByStyle[style] ?? 96;
    return { bpm, samples: synthesizeWave(notes, bpm) };
  });

  const totalSamples = segments.reduce((acc, seg) => acc + seg.samples.length, 0);
  const combined = new Float32Array(totalSamples);
  let cursor = 0;

  segments.forEach((seg) => {
    combined.set(seg.samples, cursor);
    cursor += seg.samples.length;
  });

  return encodeWav(combined, SAMPLE_RATE);
}

function resolveBpm(styles: string[]): number {
  if (!styles.length) return 96;
  const total = styles.reduce((acc, style) => acc + (tempoByStyle[style] ?? 96), 0);
  return Math.round(total / styles.length);
}

function encodeVarInt(value: number): number[] {
  const bytes = [] as number[];
  let buffer = value & 0x7f;
  while ((value >>= 7)) {
    buffer <<= 8;
    buffer |= (value & 0x7f) | 0x80;
  }
  while (true) {
    bytes.push(buffer & 0xff);
    if (buffer & 0x80) buffer >>= 8;
    else break;
  }
  return bytes;
}

function buildMidiFile(notes: string[], bpm: number): Uint8Array {
  const ticksPerBeat = 96;
  const tempo = Math.round(60_000_000 / bpm);
  const track: number[] = [];

  track.push(0x00, 0xff, 0x51, 0x03, (tempo >> 16) & 0xff, (tempo >> 8) & 0xff, tempo & 0xff);
  track.push(0x00, 0xff, 0x58, 0x04, 0x04, 0x02, 0x18, 0x08);

  notes.forEach((note) => {
    const midi = noteToMidi(note);
    track.push(0x00, 0x90, midi, 0x60);
    track.push(...encodeVarInt(ticksPerBeat / 2), 0x80, midi, 0x40);
  });

  track.push(0x00, 0xff, 0x2f, 0x00);

  const trackLength = track.length;
  const header = [
    0x4d, 0x54, 0x68, 0x64,
    0x00, 0x00, 0x00, 0x06,
    0x00, 0x00,
    0x00, 0x01,
    0x00, ticksPerBeat,
    0x4d, 0x54, 0x72, 0x6b,
    (trackLength >> 24) & 0xff,
    (trackLength >> 16) & 0xff,
    (trackLength >> 8) & 0xff,
    trackLength & 0xff,
  ];

  return new Uint8Array([...header, ...track]);
}

function downloadFile(data: Blob | Uint8Array, filename: string, type: string) {
  const blob = data instanceof Blob ? data : new Blob([data], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function updateToggleVisibility() {
  ui.customScale.style.display = ui.scalePreset.value === 'custom' ? 'block' : 'none';
  ui.medleyList.style.display = ui.medley.checked ? 'block' : 'none';
}

async function handleAnalyze() {
  const file = ui.audioUpload.files?.[0];
  if (!file) {
    setMessage('Upload an audio file to analyze.', 'warn');
    return;
  }

  try {
    setMessage('Analyzing audio fingerprint…');
    currentHash = await hashFile(file);
    const motif = ui.seedMotif.value.trim();
    currentNotes = deriveNotes(currentHash, motif);
    ui.exportMidiBtn.disabled = currentNotes.length === 0;
    setMessage(`Derived hash ${currentHash.slice(0, 12)}… → ${currentNotes.length} ritual tones.`);
  } catch (err) {
    setMessage(err instanceof Error ? err.message : 'Failed to analyze file.', 'error');
  }
}

function handleRender() {
  if (!currentHash || !currentNotes.length) {
    setMessage('Analyze an audio file first to derive the ritual melody.', 'warn');
    return;
  }

  const styles = ui.medley.checked ? parseStyles(ui.medleyList.value) : [ui.songStyle.value];
  if (!styles.length) {
    setMessage('Choose at least one valid style for playback.', 'warn');
    return;
  }

  const bpm = resolveBpm(styles);
  const wave = styles.length === 1 ? renderWave(currentNotes, bpm) : renderMedleyWave(currentNotes, styles);
  ui.keySongAudio.src = URL.createObjectURL(wave);
  ui.keySongAudio.play().catch(() => setMessage('Press play on the audio element to listen.', 'warn'));
  const descriptor = styles.length === 1 ? `${styles[0]} @ ~${bpm} BPM` : `${styles.join(' → ')} medley @ ~${bpm} BPM`;
  setMessage(`Rendered ${currentNotes.length} notes as ${descriptor}.`);
}

function handleExportMidi() {
  if (!currentNotes.length) {
    setMessage('Nothing to export — run an analysis first.', 'warn');
    return;
  }

  const styles = ui.medley.checked ? parseStyles(ui.medleyList.value) : [ui.songStyle.value];
  if (!styles.length) {
    setMessage('Choose at least one valid style to export.', 'warn');
    return;
  }

  const bpm = resolveBpm(styles);
  const midi = buildMidiFile(currentNotes, bpm);
  downloadFile(midi, 'echotome-melody.mid', 'audio/midi');

  if (ui.exportStems.checked) {
    const { lead, harmony } = buildStems(currentNotes);
    downloadFile(buildMidiFile(lead, bpm), 'echotome-stem-lead.mid', 'audio/midi');
    downloadFile(buildMidiFile(harmony, bpm), 'echotome-stem-harmony.mid', 'audio/midi');
    setMessage(`Exported MIDI plus two stems (${styles.join(', ')} @ ~${bpm} BPM).`);
    return;
  }

  setMessage(`Exported MIDI derived from the ritual hash (${styles.join(', ')} @ ~${bpm} BPM).`);
}

function monitorIntegrity() {
  if (devtoolsOpen()) {
    setMessage('Warning: devtools detected. Ritual integrity may be reduced.', 'warn');
  }
}

function bootstrap() {
  ui.analyzeBtn.addEventListener('click', handleAnalyze);
  ui.renderKeySongBtn.addEventListener('click', handleRender);
  ui.exportMidiBtn.addEventListener('click', handleExportMidi);
  ui.scalePreset.addEventListener('change', updateToggleVisibility);
  ui.medley.addEventListener('change', updateToggleVisibility);
  updateToggleVisibility();

  setInterval(monitorIntegrity, 2000);
  setMessage('Ready. Upload an audio file to derive your ritual key.');
}

bootstrap();
