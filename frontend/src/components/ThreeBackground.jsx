// frontend/src/components/ThreeBackground.jsx

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function ThreeBackground() {
  const mountRef = useRef(null);

  useEffect(() => {
    const el = mountRef.current;
    const W = window.innerWidth;
    const H = window.innerHeight;
    const mouse = { x: 0, y: 0 };

    // ── Renderer ─────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    // ── Scene + Camera ───────────────────────────────────────────────
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, W / H, 1, 2000);
    camera.position.set(0, 80, 600);

    // ── Light Source ─────────────────────────────────────────────────
    // Subtle ambient lighting matching PRISM palette
    const ambientLight = new THREE.AmbientLight(0x040409, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0x7c3aed, 1.2); // Violet highlight
    directionalLight.position.set(0, 300, 100);
    scene.add(directionalLight);

    // ── Organic Plasma Topology Mesh ──────────────────────────────────
    const GRID_SIZE = 1400;
    const SEGMENTS = 40;
    
    // Create plane geometry representing the topology mesh
    const planeGeom = new THREE.PlaneGeometry(GRID_SIZE, GRID_SIZE, SEGMENTS, SEGMENTS);
    
    // Keep track of original vertex coordinates to compute displacements
    const origPositions = planeGeom.attributes.position.array.slice();

    // Material with subtle violet wireframe and translucent navy filling
    const meshMat = new THREE.MeshBasicMaterial({
      color: 0x070514, // deep navy surface
      transparent: true,
      opacity: 0.75,
      side: THREE.DoubleSide
    });

    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x7c3aed, // Violet lines
      wireframe: true,
      transparent: true,
      opacity: 0.08,
      side: THREE.DoubleSide
    });

    const solidMesh = new THREE.Mesh(planeGeom, meshMat);
    const wireMesh = new THREE.Mesh(planeGeom, wireMat);

    // Group for positioning and tilting the landscape
    const landscapeGroup = new THREE.Group();
    landscapeGroup.add(solidMesh);
    landscapeGroup.add(wireMesh);

    // Rotate and lower the landscape to form the background mesh
    landscapeGroup.rotation.x = -Math.PI / 2.3; // tilted floor
    landscapeGroup.rotation.z = Math.PI / 16;  // organic diagonal alignment
    landscapeGroup.position.y = -260;           // lowered
    scene.add(landscapeGroup);

    // ── Animation Loop ───────────────────────────────────────────────
    let animId;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Deform vertices dynamically to generate organic waves
      const posAttr = planeGeom.attributes.position;
      const arr = posAttr.array;

      for (let i = 0; i < arr.length; i += 3) {
        const x = origPositions[i];
        const y = origPositions[i + 1];

        // Layered sine and cosine waves to create a fluid, non-repetitive "plasma" motion
        const wave1 = Math.sin(x * 0.003 + elapsed * 0.45) * 38;
        const wave2 = Math.cos(y * 0.0035 + elapsed * 0.38) * 38;
        const wave3 = Math.sin((x + y) * 0.0018 + elapsed * 0.25) * 18;

        // Apply displacement to Z coordinate (vertical height)
        arr[i + 2] = origPositions[i + 2] + wave1 + wave2 + wave3;
      }

      posAttr.needsUpdate = true;

      // Subtle parallax response to mouse movements
      camera.position.x += (mouse.x * 70 - camera.position.x) * 0.015;
      camera.position.y += ((-mouse.y * 50 + 80) - camera.position.y) * 0.015;
      camera.lookAt(new THREE.Vector3(0, -60, 0));

      renderer.render(scene, camera);
    };
    animate();

    // ── Event Listeners ──────────────────────────────────────────────
    const onMouseMove = (e) => {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener('mousemove', onMouseMove);

    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', onResize);

    // ── Cleanup ──────────────────────────────────────────────────────
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}
