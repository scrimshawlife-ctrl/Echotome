import { selfIntegrityCheck, devtoolsOpen } from './guard';
import { derivePDL } from './pdl';

// DOM elements
const audioUpload = document.getElementById('audioUpload') as HTMLInputElement;
const analyzeBtn = document.getElementById('analyzeBtn') as HTMLButtonElement;
const renderKeySongBtn = document.getElementById('renderKeySongBtn') as HTMLButtonElement;
const exportMidiBtn = document.getElementById('exportMidiBtn') as HTMLButtonElement;
const exportStems = document.getElementById('exportStems') as HTMLInputElement;
const songStyle = document.getElementById('songStyle') as HTMLSelectElement;
const seedMotif = document.getElementById('seedMotif') as HTMLInputElement;
const scalePreset = document.getElementById('scalePreset') as HTMLSelectElement;
const customScale = document.getElementById('customScale') as HTMLInputElement;
const medley = document.getElementById('medley') as HTMLInputElement;
const medleyList = document.getElementById('medleyList') as HTMLInputElement;
const keySongAudio = document.getElementById('keySongAudio') as HTMLAudioElement;
const messages = document.getElementById('messages') as HTMLDivElement;

let currentKey: Uint8Array | null = null;

// Event handlers
analyzeBtn.addEventListener('click', async () => {
  if (!audioUpload.files || audioUpload.files.length === 0) {
    showMessage('Please select an audio file first.');
    return;
  }

  showMessage('Analyzing audio...');
  
  try {
    const file = audioUpload.files[0];
    const arrayBuffer = await file.arrayBuffer();
    
    // TODO: Convert audio to MIDI and derive key
    // For now, just derive key from file buffer
    currentKey = await deriveKey(new Uint8Array(arrayBuffer));
    
    showMessage('Key generated successfully!');
    exportMidiBtn.disabled = false;
  } catch (error) {
    showMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
});

renderKeySongBtn.addEventListener('click', async () => {
  if (!currentKey) {
    showMessage('Please generate a key first.');
    return;
  }

  showMessage('Rendering key as song...');
  
  try {
    // TODO: Render key as audio using selected style
    showMessage('Song rendered! (Not yet implemented)');
  } catch (error) {
    showMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
});

exportMidiBtn.addEventListener('click', () => {
  showMessage('MIDI export not yet implemented.');
});

scalePreset.addEventListener('change', () => {
  customScale.style.display = scalePreset.value === 'custom' ? 'inline-block' : 'none';
});

medley.addEventListener('change', () => {
  medleyList.style.display = medley.checked ? 'inline-block' : 'none';
});

// Helper functions
function showMessage(msg: string) {
  messages.textContent = msg;
}

async function deriveKey(data: Uint8Array): Promise<Uint8Array> {
  // Use PDL for key derivation
  const pdlOutput = await derivePDL(data);
  
  // Hash the PDL output to get AES-256 key
  const keyMaterial = await crypto.subtle.digest('SHA-256', pdlOutput);
  return new Uint8Array(keyMaterial);
}

// Initialize
async function init() {
  // Run integrity check (for production builds)
  if (import.meta.env.PROD) {
    // Expected hash would be set during build
    const isValid = await selfIntegrityCheck('');
    if (!isValid) {
      showMessage('Warning: Integrity check failed!');
    }
  }

  // Check for devtools
  if (devtoolsOpen()) {
    console.warn('Developer tools detected');
  }

  showMessage('Ready. Upload an audio file to begin.');
}

init();
