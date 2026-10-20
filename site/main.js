import { initCosmicScene } from './scene.js';
import { toggleAudio, playUiClick } from './audio.js';

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize 3D Cosmic WebGL Scene
  const sceneHandle = initCosmicScene('bg-canvas', 'cosmic-fallback');

  // 2. Audio Toggle Setup
  const audioBtn = document.getElementById('audio-toggle-btn');
  const audioLabel = document.getElementById('audio-btn-label');

  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      const active = toggleAudio();
      audioBtn.classList.toggle('active', active);
      audioLabel.textContent = active ? 'AUDIO: RESONATING' : 'AUDIO: OFF';
      if (active) playUiClick();
    });
  }

  // 3. Telemetry Clock (UTC)
  const clockEl = document.getElementById('hud-clock');
  function updateClock() {
    if (!clockEl) return;
    const now = new Date();
    clockEl.textContent = now.toUTCString().split(' ')[4] + ' UTC';
  }
  updateClock();
  setInterval(updateClock, 1000);

  // 4. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobile-menu-btn');
  const navMenu = document.getElementById('site-navigation');

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      navMenu.classList.toggle('open');
      playUiClick();
    });

    // Close menu when link clicked
    navMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('open');
        playUiClick();
      });
    });
  }

  // 5. Copy Email Action with Toast
  const copyBtn = document.getElementById('copy-email-btn');
  const toast = document.getElementById('toast');

  if (copyBtn && toast) {
    copyBtn.addEventListener('click', async () => {
      playUiClick();
      try {
        await navigator.clipboard.writeText('novotiaproducts@gmail.com');
        showToast('COPIED: novotiaproducts@gmail.com');
      } catch (err) {
        // Fallback prompt
        showToast('ADDRESS: novotiaproducts@gmail.com');
      }
    });
  }

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2800);
  }

  // 6. Navigation Scrollspy
  const sections = document.querySelectorAll('section');
  const navLinks = document.querySelectorAll('.nav-link');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navLinks.forEach(link => {
          link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
        });
      }
    });
  }, { threshold: 0.35 });

  sections.forEach(s => observer.observe(s));

  // 7. Click sounds on interactive elements
  document.querySelectorAll('a, button').forEach(el => {
    el.addEventListener('click', () => playUiClick());
  });
});
