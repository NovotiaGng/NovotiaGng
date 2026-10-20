import * as THREE from 'three';

export function initCosmicScene(canvasId, fallbackId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  // WebGL Availability check
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
  } catch (e) {
    console.warn('WebGL initialization failed, switching to static fallback:', e);
    const fallback = document.getElementById(fallbackId);
    if (fallback) fallback.style.display = 'block';
    return null;
  }

  const width = window.innerWidth;
  const height = window.innerHeight;

  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x05060A, 0.0018);

  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
  camera.position.set(0, 0, 42);

  // ---------------------------------------------------------------
  // LIGHTING SYSTEM
  // ---------------------------------------------------------------
  const ambientLight = new THREE.AmbientLight(0x0E1326, 1.2);
  scene.add(ambientLight);

  const dirLight = new THREE.DirectionalLight(0x67E8F9, 2.5);
  dirLight.position.set(20, 40, 30);
  scene.add(dirLight);

  const pointLightViolet = new THREE.PointLight(0x8B5CF6, 4.0, 120);
  pointLightViolet.position.set(-15, 10, 15);
  scene.add(pointLightViolet);

  const pointLightMagenta = new THREE.PointLight(0xE879F9, 3.5, 100);
  pointLightMagenta.position.set(15, -12, 10);
  scene.add(pointLightMagenta);

  const pointLightCyan = new THREE.PointLight(0x67E8F9, 4.0, 110);
  pointLightCyan.position.set(0, 20, -10);
  scene.add(pointLightCyan);

  // ---------------------------------------------------------------
  // CENTRAL SYSTEM GROUP (Monolith + Orbital Rings)
  // ---------------------------------------------------------------
  const systemGroup = new THREE.Group();
  scene.add(systemGroup);

  // 1. Obsidian Central Monolith
  const monolithGroup = new THREE.Group();
  systemGroup.add(monolithGroup);

  const monolithMat = new THREE.MeshPhysicalMaterial({
    color: 0x070913,
    metalness: 0.95,
    roughness: 0.12,
    reflectivity: 0.9,
    clearcoat: 0.8,
    clearcoatRoughness: 0.1
  });

  // Main vertical spire
  const mainCoreGeo = new THREE.BoxGeometry(3.2, 14.0, 3.2);
  const mainCore = new THREE.Mesh(mainCoreGeo, monolithMat);
  monolithGroup.add(mainCore);

  // Flanking architectural pylons
  const pylonGeo = new THREE.BoxGeometry(1.4, 10.5, 1.8);
  const pylonLeft = new THREE.Mesh(pylonGeo, monolithMat);
  pylonLeft.position.set(-2.8, -0.5, 0);
  monolithGroup.add(pylonLeft);

  const pylonRight = new THREE.Mesh(pylonGeo, monolithMat);
  pylonRight.position.set(2.8, -0.5, 0);
  monolithGroup.add(pylonRight);

  // Inner Core Glowing Energy Conduit
  const coreGlowGeo = new THREE.CylinderGeometry(0.5, 0.5, 15, 16);
  const coreGlowMat = new THREE.MeshBasicMaterial({
    color: 0x67E8F9,
    wireframe: true,
    transparent: true,
    opacity: 0.35
  });
  const coreGlow = new THREE.Mesh(coreGlowGeo, coreGlowMat);
  monolithGroup.add(coreGlow);

  // Luminous Edge Outlines
  const edgeGeo = new THREE.EdgesGeometry(mainCoreGeo);
  const edgeMat = new THREE.LineBasicMaterial({
    color: 0x8B5CF6,
    transparent: true,
    opacity: 0.65
  });
  const edgeLines = new THREE.LineSegments(edgeGeo, edgeMat);
  monolithGroup.add(edgeLines);

  // 2. Orbital Rings
  const ringMaterials = [
    new THREE.MeshPhysicalMaterial({
      color: 0x67E8F9,
      metalness: 0.9,
      roughness: 0.2,
      emissive: 0x22D3EE,
      emissiveIntensity: 0.25,
      wireframe: false
    }),
    new THREE.MeshPhysicalMaterial({
      color: 0x8B5CF6,
      metalness: 0.85,
      roughness: 0.25,
      emissive: 0x7C3AED,
      emissiveIntensity: 0.25
    }),
    new THREE.MeshPhysicalMaterial({
      color: 0xE879F9,
      metalness: 0.95,
      roughness: 0.15,
      emissive: 0xD946EF,
      emissiveIntensity: 0.2
    })
  ];

  const rings = [];
  const ringConfigs = [
    { radius: 11.0, tube: 0.08, rotX: 1.25, rotY: 0.35, speed: 0.004, mat: 0 },
    { radius: 14.5, tube: 0.06, rotX: -0.95, rotY: 0.75, speed: -0.003, mat: 1 },
    { radius: 18.0, tube: 0.07, rotX: 0.65, rotY: -0.85, speed: 0.002, mat: 2 }
  ];

  ringConfigs.forEach(cfg => {
    const ringGeo = new THREE.TorusGeometry(cfg.radius, cfg.tube, 16, 120);
    const ringMesh = new THREE.Mesh(ringGeo, ringMaterials[cfg.mat]);
    ringMesh.rotation.x = cfg.rotX;
    ringMesh.rotation.y = cfg.rotY;
    systemGroup.add(ringMesh);
    rings.push({ mesh: ringMesh, speed: cfg.speed });
  });

  // 3. Floating Geometric Polyhedra & Satellites
  const satellites = [];
  const satMat = new THREE.MeshPhysicalMaterial({
    color: 0x1E1B4B,
    metalness: 0.95,
    roughness: 0.1,
    clearcoat: 1.0,
    reflectivity: 1.0
  });

  const satGeos = [
    new THREE.IcosahedronGeometry(0.9, 0),
    new THREE.OctahedronGeometry(1.1, 0),
    new THREE.DodecahedronGeometry(0.8, 0),
    new THREE.SphereGeometry(0.7, 24, 24)
  ];

  for (let i = 0; i < 9; i++) {
    const geo = satGeos[i % satGeos.length];
    const mesh = new THREE.Mesh(geo, satMat);

    // Glowing edges for geometric satellites
    if (i % 2 === 0) {
      const satEdge = new THREE.LineSegments(
        new THREE.EdgesGeometry(geo),
        new THREE.LineBasicMaterial({
          color: i % 4 === 0 ? 0x67E8F9 : 0x8B5CF6,
          transparent: true,
          opacity: 0.8
        })
      );
      mesh.add(satEdge);
    }

    const orbitRadius = 10 + Math.random() * 14;
    const orbitSpeed = (0.002 + Math.random() * 0.004) * (Math.random() > 0.5 ? 1 : -1);
    const orbitAngle = Math.random() * Math.PI * 2;
    const yOffset = (Math.random() - 0.5) * 16;

    systemGroup.add(mesh);
    satellites.push({
      mesh,
      orbitRadius,
      orbitSpeed,
      orbitAngle,
      yOffset,
      rotSpeedX: (Math.random() - 0.5) * 0.02,
      rotSpeedY: (Math.random() - 0.5) * 0.02
    });
  }

  // ---------------------------------------------------------------
  // DEEP-SPACE PARTICLE STARFIELD (3,000 points)
  // ---------------------------------------------------------------
  const starCount = 3200;
  const starGeometry = new THREE.BufferGeometry();
  const starPositions = new Float32Array(starCount * 3);
  const starColors = new Float32Array(starCount * 3);

  const colorPalette = [
    new THREE.Color(0x67E8F9), // Laser Cyan
    new THREE.Color(0x8B5CF6), // Electric Violet
    new THREE.Color(0xE879F9), // Plasma Magenta
    new THREE.Color(0xFFFFFF), // Pure White
    new THREE.Color(0xC4B5FD)  // Soft Lavender
  ];

  for (let i = 0; i < starCount; i++) {
    const i3 = i * 3;
    const radius = 60 + Math.random() * 450;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);

    starPositions[i3] = radius * Math.sin(phi) * Math.cos(theta);
    starPositions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
    starPositions[i3 + 2] = radius * Math.cos(phi);

    const chosenColor = colorPalette[Math.floor(Math.random() * colorPalette.length)];
    starColors[i3] = chosenColor.r;
    starColors[i3 + 1] = chosenColor.g;
    starColors[i3 + 2] = chosenColor.b;
  }

  starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
  starGeometry.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

  const starMaterial = new THREE.PointsMaterial({
    size: 1.4,
    vertexColors: true,
    transparent: true,
    opacity: 0.85,
    sizeAttenuation: true
  });

  const starField = new THREE.Points(starGeometry, starMaterial);
  scene.add(starField);

  // ---------------------------------------------------------------
  // VOLUMETRIC NEBULA FIELD (Soft Particle Clouds)
  // ---------------------------------------------------------------
  const nebulaCount = 500;
  const nebulaGeo = new THREE.BufferGeometry();
  const nebulaPos = new Float32Array(nebulaCount * 3);
  const nebulaCols = new Float32Array(nebulaCount * 3);

  for (let i = 0; i < nebulaCount; i++) {
    const i3 = i * 3;
    const dist = 30 + Math.random() * 90;
    const angle = Math.random() * Math.PI * 2;

    nebulaPos[i3] = Math.cos(angle) * dist;
    nebulaPos[i3 + 1] = (Math.random() - 0.5) * 45;
    nebulaPos[i3 + 2] = Math.sin(angle) * dist - 30;

    const col = (i % 2 === 0) ? new THREE.Color(0x8B5CF6) : new THREE.Color(0x67E8F9);
    nebulaCols[i3] = col.r;
    nebulaCols[i3 + 1] = col.g;
    nebulaCols[i3 + 2] = col.b;
  }

  nebulaGeo.setAttribute('position', new THREE.BufferAttribute(nebulaPos, 3));
  nebulaGeo.setAttribute('color', new THREE.BufferAttribute(nebulaCols, 3));

  const nebulaMat = new THREE.PointsMaterial({
    size: 5.5,
    vertexColors: true,
    transparent: true,
    opacity: 0.35,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true
  });

  const nebula = new THREE.Points(nebulaGeo, nebulaMat);
  scene.add(nebula);

  // ---------------------------------------------------------------
  // INTERACTION & CAMERA DYNAMICS
  // ---------------------------------------------------------------
  let mouseX = 0;
  let mouseY = 0;
  let targetMouseX = 0;
  let targetMouseY = 0;
  let scrollProgress = 0;

  function onMouseMove(event) {
    targetMouseX = (event.clientX / window.innerWidth - 0.5) * 2;
    targetMouseY = (event.clientY / window.innerHeight - 0.5) * 2;
  }
  window.addEventListener('mousemove', onMouseMove, { passive: true });

  function onScroll() {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    scrollProgress = maxScroll > 0 ? window.scrollY / maxScroll : 0;
  }
  window.addEventListener('scroll', onScroll, { passive: true });

  // ---------------------------------------------------------------
  // ANIMATION LOOP
  // ---------------------------------------------------------------
  let clock = new THREE.Clock();
  let animationFrameId = null;
  let isRunning = true;

  function animate() {
    if (!isRunning) return;
    animationFrameId = requestAnimationFrame(animate);

    const delta = clock.getDelta();
    const elapsedTime = clock.getElapsedTime();

    // Smooth mouse lerping
    mouseX += (targetMouseX - mouseX) * 0.05;
    mouseY += (targetMouseY - mouseY) * 0.05;

    // Rotate system slightly with mouse parallax
    systemGroup.rotation.y = elapsedTime * 0.08 + mouseX * 0.25;
    systemGroup.rotation.x = mouseY * 0.15;

    // Rotate Monolith core
    monolithGroup.rotation.y = Math.sin(elapsedTime * 0.3) * 0.15;
    coreGlow.rotation.y += delta * 0.5;

    // Animate orbital rings
    rings.forEach(r => {
      r.mesh.rotation.z += r.speed;
    });

    // Animate orbiting satellites
    satellites.forEach(s => {
      s.orbitAngle += s.orbitSpeed;
      s.mesh.position.x = Math.cos(s.orbitAngle) * s.orbitRadius;
      s.mesh.position.z = Math.sin(s.orbitAngle) * s.orbitRadius;
      s.mesh.position.y = s.yOffset + Math.sin(elapsedTime * 1.5 + s.orbitRadius) * 1.5;
      s.mesh.rotation.x += s.rotSpeedX;
      s.mesh.rotation.y += s.rotSpeedY;
    });

    // Orbit point lights for dynamic reflections
    pointLightCyan.position.x = Math.sin(elapsedTime * 0.6) * 22;
    pointLightCyan.position.z = Math.cos(elapsedTime * 0.6) * 22;

    pointLightViolet.position.x = Math.cos(elapsedTime * 0.4) * 24;
    pointLightViolet.position.y = Math.sin(elapsedTime * 0.4) * 18;

    pointLightMagenta.position.z = Math.sin(elapsedTime * 0.5) * 20;
    pointLightMagenta.position.x = -Math.cos(elapsedTime * 0.5) * 20;

    // Slow starfield rotation
    starField.rotation.y = elapsedTime * 0.012;
    nebula.rotation.y = -elapsedTime * 0.018;

    // Scroll-driven camera path: gently dives forward and changes perspective
    const targetCamZ = 42 - scrollProgress * 18;
    const targetCamY = -scrollProgress * 25 + mouseY * 2;
    camera.position.z += (targetCamZ - camera.position.z) * 0.08;
    camera.position.y += (targetCamY - camera.position.y) * 0.08;
    camera.position.x += (mouseX * 4 - camera.position.x) * 0.08;
    camera.lookAt(0, -scrollProgress * 15, 0);

    renderer.render(scene, camera);
  }

  animate();

  // ---------------------------------------------------------------
  // RESIZE & VISIBILITY HANDLERS
  // ---------------------------------------------------------------
  function onWindowResize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  }
  window.addEventListener('resize', onWindowResize);

  function onVisibilityChange() {
    if (document.hidden) {
      isRunning = false;
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    } else {
      if (!isRunning) {
        isRunning = true;
        clock.getDelta(); // reset delta to prevent huge jumps
        animate();
      }
    }
  }
  document.addEventListener('visibilitychange', onVisibilityChange);

  // Return clean teardown handle
  return {
    destroy: () => {
      isRunning = false;
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onWindowResize);
      document.removeEventListener('visibilitychange', onVisibilityChange);
      renderer.dispose();
    }
  };
}
