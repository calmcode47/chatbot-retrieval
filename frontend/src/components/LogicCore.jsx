// frontend/src/components/LogicCore.jsx

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function LogicCore({ isHovered = false }) {
  const mountRef = useRef(null);
  const hoveredRef = useRef(isHovered);

  useEffect(() => {
    hoveredRef.current = isHovered;
  }, [isHovered]);

  useEffect(() => {
    const el = mountRef.current;
    const SIZE = 440; // canvas dimensions

    // ── Renderer ─────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(SIZE, SIZE);
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    // ── Scene + Camera ───────────────────────────────────────────────
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    camera.position.set(0, 0, 5.5);

    // ── Lighting ─────────────────────────────────────────────────────
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.15);
    scene.add(ambientLight);

    // Dynamic point lights mapping to the split-spectrum theme
    const violetLight = new THREE.PointLight(0x7c3aed, 3, 12);
    violetLight.position.set(-2, 2, 2);
    scene.add(violetLight);

    const cyanLight = new THREE.PointLight(0x0ea5e9, 3, 12);
    cyanLight.position.set(2, -2, 2);
    scene.add(cyanLight);

    // ── Central Light Source (Logic Core Center) ──────────────────────
    const centerGroup = new THREE.Group();
    
    // Core glow center
    const coreGeom = new THREE.SphereGeometry(0.18, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x0ea5e9, // Cyan core
    });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    centerGroup.add(coreMesh);

    // Translucent outer shell for core pulse
    const shellGeom = new THREE.SphereGeometry(0.35, 16, 16);
    const shellMat = new THREE.MeshBasicMaterial({
      color: 0x7c3aed,
      transparent: true,
      opacity: 0.18,
      wireframe: true
    });
    const shellMesh = new THREE.Mesh(shellGeom, shellMat);
    centerGroup.add(shellMesh);

    scene.add(centerGroup);

    // ── Orbiting Tetrahedra (The 5 structural elements) ──────────────
    const TETRA_COUNT = 5;
    const tetraGroup = new THREE.Group();
    const tetras = [];
    const connectionLines = [];

    // Distinct split-spectrum colors representing light dispersion
    const colors = [
      0x7c3aed, // Void Violet
      0x8b5cf6, // Medium Violet
      0xa78bfa, // Violet Soft
      0x38bdf8, // Light Cyan
      0x0ea5e9, // Pure Cyan
    ];

    const lineMat = new THREE.LineBasicMaterial({
      color: 0x7c3aed,
      transparent: true,
      opacity: 0.12,
    });

    for (let i = 0; i < TETRA_COUNT; i++) {
      const radius = 1.2 + (i * 0.28); // Staggered orbital distances
      const size = 0.22 + (Math.random() * 0.08); // Unique sizes

      const geom = new THREE.TetrahedronGeometry(size, 0);
      const mat = new THREE.MeshStandardMaterial({
        color: colors[i],
        roughness: 0.05,
        metalness: 0.9,
        transparent: true,
        opacity: 0.65,
        emissive: colors[i],
        emissiveIntensity: 0.25,
        flatShading: true,
      });

      const tetraMesh = new THREE.Mesh(geom, mat);

      // Create sharp wireframe outline for premium scientific aesthetic
      const edges = new THREE.EdgesGeometry(geom);
      const edgeLine = new THREE.LineSegments(
        edges,
        new THREE.LineBasicMaterial({ color: colors[i], transparent: true, opacity: 0.85 })
      );
      tetraMesh.add(edgeLine);

      // Orbital axis and speed setup
      // Stagger orbital axes to create interlocking, non-colliding shells
      const angleOffset = (i * Math.PI * 2) / TETRA_COUNT;
      const axis = new THREE.Vector3(
        Math.sin(angleOffset * 1.5),
        Math.cos(angleOffset),
        Math.sin(angleOffset * 0.5)
      ).normalize();

      tetraMesh.userData = {
        radius,
        axis,
        speed: 0.005 + (i * 0.002), // Staggered speed
        rotSpeedX: 0.01 + Math.random() * 0.01,
        rotSpeedY: 0.01 + Math.random() * 0.01,
        angle: Math.random() * Math.PI * 2
      };

      tetraGroup.add(tetraMesh);
      tetras.push(tetraMesh);

      // Connecting beam from center to tetrahedron
      const lineGeom = new THREE.BufferGeometry();
      const linePositions = new Float32Array(6); // 2 vertices × 3 coordinates
      lineGeom.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
      const connLine = new THREE.Line(lineGeom, lineMat);
      tetraGroup.add(connLine);
      connectionLines.push({ line: connLine, positions: linePositions, target: tetraMesh });
    }

    scene.add(tetraGroup);

    // ── Animation Loop ───────────────────────────────────────────────
    let animId;
    let time = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time += 0.01;

      const speedMultiplier = hoveredRef.current ? 2.5 : 1.0;

      // Pulse the central logic light core
      const coreScale = 1.0 + Math.sin(time * 3.5) * 0.08;
      coreMesh.scale.setScalar(coreScale);
      shellMesh.scale.setScalar(1.0 + Math.cos(time * 2.0) * 0.05);
      shellMesh.rotation.y += 0.004 * speedMultiplier;

      // Animate tetrahedra orbits
      tetras.forEach((tetra, i) => {
        const u = tetra.userData;
        u.angle += u.speed * speedMultiplier;

        // Calculate 3D position based on axis and angle
        const cosAngle = Math.cos(u.angle);
        const sinAngle = Math.sin(u.angle);

        // Orthogonal vectors to build the plane of orbit
        const uVec = new THREE.Vector3().crossVectors(u.axis, new THREE.Vector3(0, 1, 0)).normalize();
        if (uVec.lengthSq() < 0.1) {
          uVec.crossVectors(u.axis, new THREE.Vector3(1, 0, 0)).normalize();
        }
        const vVec = new THREE.Vector3().crossVectors(u.axis, uVec).normalize();

        const position = new THREE.Vector3()
          .addScaledVector(uVec, cosAngle * u.radius)
          .addScaledVector(vVec, sinAngle * u.radius);

        tetra.position.copy(position);

        // Spin the tetrahedron itself
        tetra.rotation.x += u.rotSpeedX * speedMultiplier;
        tetra.rotation.y += u.rotSpeedY * speedMultiplier;
      });

      // Update structural connection filaments
      connectionLines.forEach(({ line, positions, target }) => {
        // Start filament at tetrahedron position
        positions[0] = target.position.x;
        positions[1] = target.position.y;
        positions[2] = target.position.z;
        // End filament at central point of light (0,0,0)
        positions[3] = 0;
        positions[4] = 0;
        positions[5] = 0;
        line.geometry.attributes.position.needsUpdate = true;
      });

      // Rotate group for additional parallax effect
      tetraGroup.rotation.y = Math.sin(time * 0.25) * 0.12;

      renderer.render(scene, camera);
    };
    animate();

    // ── Cleanup ──────────────────────────────────────────────────────
    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{
        width: 440,
        height: 440,
        cursor: 'pointer',
        filter: 'drop-shadow(0 0 45px rgba(124, 58, 237, 0.15))',
      }}
    />
  );
}
