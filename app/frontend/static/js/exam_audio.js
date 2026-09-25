/**
 * EnglishMate - Exam Sound Effects Engine
 * Supports Web Audio API synthesis & HTML5 Audio fallback for zero-latency in-browser exam audio.
 */
(function(window) {
  'use strict';

  class ExamSoundEffects {
    constructor() {
      this.enabled = true;
      this.audioCache = {};
      this.ctx = null;
      this.initAudioContext();
    }

    initAudioContext() {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          this.ctx = new AudioCtx();
        }
      } catch (e) {
        this.ctx = null;
      }
    }

    resumeContext() {
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {});
      }
    }

    setEnabled(val) {
      this.enabled = Boolean(val);
    }

    // 1. Click / Select Answer Sound
    playSelect() {
      if (!this.enabled) return;
      this.resumeContext();

      if (this.ctx) {
        try {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.type = 'sine';
          osc.frequency.setValueAtTime(540, this.ctx.currentTime);
          osc.frequency.exponentialRampToValueAtTime(780, this.ctx.currentTime + 0.06);
          gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.07);
          osc.start();
          osc.stop(this.ctx.currentTime + 0.07);
          return;
        } catch (e) {}
      }
      this.playFileAudio('/static/sounds/select.wav');
    }

    // 2. Countdown Tick Sound (for last 10 seconds)
    playTick() {
      if (!this.enabled) return;
      this.resumeContext();

      if (this.ctx) {
        try {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(1100, this.ctx.currentTime);
          osc.frequency.exponentialRampToValueAtTime(400, this.ctx.currentTime + 0.04);
          gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
          gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.045);
          osc.start();
          osc.stop(this.ctx.currentTime + 0.045);
          return;
        } catch (e) {}
      }
      this.playFileAudio('/static/sounds/tick.wav');
    }

    // 3. Timeout Warning Chime
    playTimeout() {
      if (!this.enabled) return;
      this.resumeContext();

      if (this.ctx) {
        try {
          [880, 660, 440].forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.type = 'sawtooth';
            const startTime = this.ctx.currentTime + idx * 0.12;
            osc.frequency.setValueAtTime(freq, startTime);
            gain.gain.setValueAtTime(0.06, startTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.11);
            osc.start(startTime);
            osc.stop(startTime + 0.11);
          });
          return;
        } catch (e) {}
      }
      this.playFileAudio('/static/sounds/timeout.wav');
    }

    // 4. Submit Success Chime
    playSubmit() {
      if (!this.enabled) return;
      this.resumeContext();

      if (this.ctx) {
        try {
          // Major arpeggio C5 -> E5 -> G5 -> C6
          const notes = [523.25, 659.25, 783.99, 1046.50];
          notes.forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.type = 'sine';
            const startTime = this.ctx.currentTime + idx * 0.09;
            osc.frequency.setValueAtTime(freq, startTime);
            gain.gain.setValueAtTime(0.05, startTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.28);
            osc.start(startTime);
            osc.stop(startTime + 0.28);
          });
          return;
        } catch (e) {}
      }
      this.playFileAudio('/static/sounds/success.wav');
    }

    playFileAudio(url) {
      try {
        const audio = new Audio(url);
        audio.volume = 0.5;
        audio.play().catch(() => {});
      } catch (e) {}
    }
  }

  window.ExamSoundEffects = new ExamSoundEffects();

  // Unlock AudioContext on first user interaction in document
  const unlockAudio = () => {
    if (window.ExamSoundEffects) {
      window.ExamSoundEffects.resumeContext();
    }
    document.removeEventListener('click', unlockAudio);
    document.removeEventListener('keydown', unlockAudio);
  };
  document.addEventListener('click', unlockAudio);
  document.addEventListener('keydown', unlockAudio);
})(window);
