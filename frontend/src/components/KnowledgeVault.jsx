// frontend/src/components/KnowledgeVault.jsx

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function KnowledgeVault({ isHovered = false }) {
  const mountRef    = useRef(null);
  const hoveredRef  = useRef(isHovered);

  useEffect(() => {
    hoveredRef.current = isHovered;
  }, [isHovered]);

  useEffect(() => {
    const el = mountRef.current;
    const SIZE = 440;   // canvas size

    // ── Renderer ─────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(SIZE, SIZE);
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    // ── Scene + Camera ───────────────────────────────────────────────
    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 1000);
    camera.position.set(0, 0, 5);

    // ── Lighting ─────────────────────────────────────────────────────
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0xf59e0b, 2, 10);
    pointLight.position.set(2, 2, 3);
    scene.add(pointLight);

    // ── Outer Icosahedron Wireframe ───────────────────────────────────
    const icoGeom = new THREE.IcosahedronGeometry(2.2, 1);
    const icoMat  = new THREE.MeshBasicMaterial({
      color:       0xf59e0b,
      wireframe:   true,
      transparent: true,
      opacity:     0.28,
    });
    const icosahedron = new THREE.Mesh(icoGeom, icoMat);
    scene.add(icosahedron);

    // Second, slightly larger shell at lower opacity
    const icoOuter = new THREE.Mesh(
      new THREE.IcosahedronGeometry(2.6, 1),
      new THREE.MeshBasicMaterial({ color: 0xf59e0b, wireframe: true, transparent: true, opacity: 0.08 })
    );
    scene.add(icoOuter);

    // ── Inner Core ───────────────────────────────────────────────────
    const coreGeom = new THREE.SphereGeometry(0.38, 24, 24);
    const coreMat  = new THREE.MeshStandardMaterial({
      color:     0xf97316,
      emissive:  0xf59e0b,
      emissiveIntensity: 0.6,
      roughness: 0.3,
      metalness: 0.7,
    });
    const core = new THREE.Mesh(coreGeom, coreMat);
    scene.add(core);

    // ── Orbiting Data Nodes ───────────────────────────────────────────
    const ORBIT_COUNT = 13;
    const orbitGroup  = new THREE.Group();
    const orbitNodes  = [];
    const orbitLines  = [];

    const nodeMat = new THREE.MeshStandardMaterial({
      color:     0xfbbf24,
      emissive:  0xf59e0b,
      emissiveIntensity: 0.4,
      roughness: 0.4,
      metalness: 0.6,
    });

    const lineMat = new THREE.LineBasicMaterial({
      color:       0xf59e0b,
      transparent: true,
      opacity:     0.18,
    });

    for (let i = 0; i < ORBIT_COUNT; i++) {
      // Random point on a sphere of radius 1.2–1.6
      const radius    = 1.2 + Math.random() * 0.4;
      const theta     = Math.random() * Math.PI * 2;
      const phi       = Math.acos(2 * Math.random() - 1);
      const nodeSize  = 0.045 + Math.random() * 0.04;

      const nodeGeom = new THREE.SphereGeometry(nodeSize, 8, 8);
      const node     = new THREE.Mesh(nodeGeom, nodeMat);

      node.position.set(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi)
      );

      // Store orbital parameters for animation
      node.userData = {
        radius,
        theta,
        phi,
        orbitSpeed:  0.004 + Math.random() * 0.006,
        orbitAxis:   new THREE.Vector3(
          Math.random() - 0.5,
          Math.random() - 0.5,
          Math.random() - 0.5
        ).normalize(),
      };

      orbitGroup.add(node);
      orbitNodes.push(node);

      // Line from node to core
      const lineGeom     = new THREE.BufferGeometry();
      const linePositions = new Float32Array(6);  // 2 points × 3
      lineGeom.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
      const line = new THREE.Line(lineGeom, lineMat);
      orbitGroup.add(line);
      orbitLines.push({ line, linePositions, nodeRef: node });
    }

    scene.add(orbitGroup);

    // ── Animation ────────────────────────────────────────────────────
    let animId;
    const rotAxis = new THREE.Vector3(0.2, 1, 0.15).normalize();
    let  time     = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time  += 0.008;

      const speedMult = hoveredRef.current ? 2.2 : 1.0;

      // Rotate outer shells
      icosahedron.rotateOnAxis(rotAxis, 0.003 * speedMult);
      icoOuter.rotateOnAxis(new THREE.Vector3(-0.1, 0.8, 0.3).normalize(), 0.002 * speedMult);

      // Pulse core
      const pulse = 1 + Math.sin(time * 2.5) * 0.06;
      core.scale.setScalar(pulse);
      coreMat.emissiveIntensity = 0.6 + Math.sin(time * 2.5) * 0.2;

      // Orbit nodes
      orbitNodes.forEach((node) => {
        node.rotateOnAxis(node.userData.orbitAxis, node.userData.orbitSpeed * speedMult);
      });

      // Update connection lines
      orbitLines.forEach(({ line, linePositions, nodeRef }) => {
        linePositions[0] = nodeRef.position.x;
        linePositions[1] = nodeRef.position.y;
        linePositions[2] = nodeRef.position.z;
        // Line ends at core (0,0,0) relative to orbitGroup
        linePositions[3] = 0;
        linePositions[4] = 0;
        linePositions[5] = 0;
        line.geometry.attributes.position.needsUpdate = true;
      });

      // Pulse wireframe opacity on hover
      icoMat.opacity = hoveredRef.current
        ? 0.45 + Math.sin(time * 4) * 0.1
        : 0.28;

      renderer.render(scene, camera);
    };
    animate();

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
        width:  440,
        height: 440,
        cursor: 'crosshair',
        filter: 'drop-shadow(0 0 40px rgba(245, 158, 11, 0.18))',
      }}
    />
  );
}
