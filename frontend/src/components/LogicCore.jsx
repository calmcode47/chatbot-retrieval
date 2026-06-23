import { useEffect, useRef } from 'react';
import * as THREE from 'three';

// Orbital parameters for 5 tetrahedra
const TETRAHEDRA = [
  { radius:1.55, orbitSpeed:0.013, selfSpeed:0.022, incline:0.00, phase:0.00,           size:0.44, color:0x7c3aed },
  { radius:1.90, orbitSpeed:0.009, selfSpeed:0.018, incline:0.52, phase:Math.PI*0.40,  size:0.38, color:0xa78bfa },
  { radius:1.70, orbitSpeed:0.016, selfSpeed:0.025, incline:0.88, phase:Math.PI*0.80,  size:0.41, color:0x0ea5e9 },
  { radius:2.10, orbitSpeed:0.007, selfSpeed:0.015, incline:-0.60, phase:Math.PI*1.20, size:0.36, color:0xc4b5fd },
  { radius:1.80, orbitSpeed:0.011, selfSpeed:0.020, incline:0.32, phase:Math.PI*1.65,  size:0.43, color:0x7c3aed },
];

export default function LogicCore({ isHovered = false }) {
  const mountRef   = useRef(null);
  const hoveredRef = useRef(isHovered);
  useEffect(() => { hoveredRef.current = isHovered; }, [isHovered]);

  useEffect(() => {
    const el   = mountRef.current;
    const SIZE = 480;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(SIZE, SIZE);
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 100);
    camera.position.set(0, 0, 7);

    // ── Lighting ─────────────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0xffffff, 0.25));
    const pointA = new THREE.PointLight(0x7c3aed, 3, 14);
    pointA.position.set(3, 3, 4);
    scene.add(pointA);
    const pointB = new THREE.PointLight(0x0ea5e9, 1.5, 10);
    pointB.position.set(-3, -2, 3);
    scene.add(pointB);

    // ── Central glow sphere ──────────────────────────────────────────
    const coreMat = new THREE.MeshStandardMaterial({
      color:     0xc4b5fd,
      emissive:  0x7c3aed,
      emissiveIntensity: 1.2,
      roughness: 0.1,
      metalness: 0.9,
    });
    const core = new THREE.Mesh(new THREE.SphereGeometry(0.10, 16, 16), coreMat);
    scene.add(core);

    // ── Tetrahedra + orbital rings ───────────────────────────────────
    const tetMeshes   = [];

    TETRAHEDRA.forEach((params) => {
      // Orbital pivot group — rotating this moves tetrahedron along orbit
      const pivot = new THREE.Group();
      pivot.rotation.z = params.incline;
      scene.add(pivot);

      // Tetrahedron wireframe
      const geo  = new THREE.TetrahedronGeometry(params.size, 0);
      const mat  = new THREE.MeshStandardMaterial({
        color:       params.color,
        emissive:    params.color,
        emissiveIntensity: 0.3,
        wireframe:   true,
        transparent: true,
        opacity:     0.75,
      });
      const tet = new THREE.Mesh(geo, mat);
      tet.position.x = params.radius;

      // Thin orbital ring
      const ringGeo = new THREE.TorusGeometry(params.radius, 0.006, 4, 80);
      const ringMat = new THREE.MeshBasicMaterial({
        color:       params.color,
        transparent: true,
        opacity:     0.14,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      scene.add(ring);
      ring.rotation.x = Math.PI / 2;
      ring.rotation.z = params.incline;

      pivot.add(tet);
      pivot.rotation.y = params.phase;

      tetMeshes.push({ tet, pivot, params });
    });

    // ── Animation ────────────────────────────────────────────────────
    let animId, time = 0;

    // Self-rotation axes (pre-computed random for each tetrahedron)
    const selfAxes = TETRAHEDRA.map(() =>
      new THREE.Vector3(Math.random()-0.5, Math.random()-0.5, Math.random()-0.5).normalize()
    );

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time  += 0.008;

      const speed = hoveredRef.current ? 1.8 : 1.0;

      // Orbit + self-rotate each tetrahedron
      tetMeshes.forEach(({ tet, pivot, params }, i) => {
        pivot.rotation.y += params.orbitSpeed * speed;
        tet.rotateOnAxis(selfAxes[i], params.selfSpeed * speed);
      });

      // Core pulse
      const p = 1 + Math.sin(time * 3) * 0.12;
      core.scale.setScalar(p);
      coreMat.emissiveIntensity = 1.2 + Math.sin(time * 3) * 0.4;

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
        width:  480,
        height: 480,
        filter: 'drop-shadow(0 0 48px rgba(124,58,237,0.20))',
      }}
    />
  );
}
