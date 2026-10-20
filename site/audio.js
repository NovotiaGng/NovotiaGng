// Web Audio API procedural cosmic audio engine (no external audio files required)

let audioCtx = null;
let masterGain = null;
let droneOsc1 = null;
let droneOsc2 = null;
let subOsc = null;
let filter = null;
let lfo = null;
let isAudioActive = false;

export function toggleAudio() {
  if (!audioCtx) {
    initAudioEngine();
  }

  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }

  isAudioActive = !isAudioActive;

  if (isAudioActive) {
    // Fade in over 1.5 seconds
    const now = audioCtx.currentTime;
    masterGain.gain.cancelScheduledValues(now);
    masterGain.gain.setValueAtTime(masterGain.gain.value, now);
    masterGain.gain.linearRampToValueAtTime(0.08, now + 1.5);
  } else {
    // Fade out over 0.8 seconds
    const now = audioCtx.currentTime;
    masterGain.gain.cancelScheduledValues(now);
    masterGain.gain.setValueAtTime(masterGain.gain.value, now);
    masterGain.gain.linearRampToValueAtTime(0.0001, now + 0.8);
  }

  return isAudioActive;
}

export function playUiClick() {
  if (!isAudioActive || !audioCtx) return;
  try {
    const now = audioCtx.currentTime;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1200, now);
    osc.frequency.exponentialRampToValueAtTime(400, now + 0.06);

    gain.gain.setValueAtTime(0.04, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(now);
    osc.stop(now + 0.07);
  } catch (e) {
    // ignore
  }
}

function initAudioEngine() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  audioCtx = new AudioContext();

  masterGain = audioCtx.createGain();
  masterGain.gain.setValueAtTime(0.0001, audioCtx.currentTime);

  // Lowpass filter for warm atmospheric space drone
  filter = audioCtx.createBiquadFilter();
  filter.type = 'lowpass';
  filter.frequency.setValueAtTime(320, audioCtx.currentTime);
  filter.Q.setValueAtTime(3.5, audioCtx.currentTime);

  // LFO modulating filter cutoff
  lfo = audioCtx.createOscillator();
  const lfoGain = audioCtx.createGain();
  lfo.frequency.setValueAtTime(0.12, audioCtx.currentTime); // 0.12 Hz slow breath
  lfoGain.gain.setValueAtTime(140, audioCtx.currentTime);
  lfo.connect(lfoGain);
  lfoGain.connect(filter.frequency);

  // Fundamental Drone (A = 108Hz, harmonic of 432Hz)
  droneOsc1 = audioCtx.createOscillator();
  droneOsc1.type = 'sawtooth';
  droneOsc1.frequency.setValueAtTime(108, audioCtx.currentTime);

  // Detuned Harmony (108.4 Hz for gentle binaural beating)
  droneOsc2 = audioCtx.createOscillator();
  droneOsc2.type = 'sine';
  droneOsc2.frequency.setValueAtTime(108.45, audioCtx.currentTime);

  // Deep Sub Bass (54 Hz)
  subOsc = audioCtx.createOscillator();
  subOsc.type = 'sine';
  subOsc.frequency.setValueAtTime(54, audioCtx.currentTime);

  const subGain = audioCtx.createGain();
  subGain.gain.setValueAtTime(0.6, audioCtx.currentTime);

  droneOsc1.connect(filter);
  droneOsc2.connect(filter);
  subOsc.connect(subGain);
  subGain.connect(filter);

  filter.connect(masterGain);
  masterGain.connect(audioCtx.destination);

  lfo.start();
  droneOsc1.start();
  droneOsc2.start();
  subOsc.start();
}
