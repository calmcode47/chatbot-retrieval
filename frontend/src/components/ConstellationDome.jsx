import { useEffect, useRef } from 'react';
import * as THREE from 'three';

// 24 dome nodes: distributed across a hemisphere
// Each has a label (shown in UI), position on dome, color class
const DOME_NODES = [
  { label: 'PDF',      color: 0x7c3aed, size: 0.090 },
  { label: 'Research', color: 0xa78bfa, size: 0.075 },
  { label: 'Policy',   color: 0x7c3aed, size: 0.082 },
  { label: 'Manual',   color: 0x0ea5e9, size: 0.078 },
  { label: 'TXT',      color: 0xc4b5fd, size: 0.070 },
  { label: 'Legal',    color: 0xa78bfa, size: 0.085 },
  { label: 'Report',   color: 0x7c3aed, size: 0.080 },
  { label: 'Notes',    color: 0x0ea5e9, size: 0.068 },
  { label: 'FAQ',      color: 0xc4b5fd, size: 0.073 },
  { label: 'Code',     color: 0x7c3aed, size: 0.076 },
  { label: 'Email',    color: 0xa78bfa, size: 0.071 },
  { label: 'CSV',      color: 0x0ea5e9, size: 0.069 },
  { label: 'API Doc',  color: 0x7c3aed, size: 0.083 },
  { label: 'Design',   color: 0xc4b5fd, size: 0.074 },
  { label: 'Spec',     color: 0xa78bfa, size: 0.077 },
  { label: 'Meeting',  color: 0x7c3aed, size: 0.072 },
  { label: 'Log',      color: 0x0ea5e9, size: 0.066 },
  { label: 'Config',   color: 0xc4b5fd, size: 0.079 },
  { label: 'Invoice',  color: 0xa78bfa, size: 0.071 },
  { label: 'Contract', color: 0x7c3aed, size: 0.086 },
  { label: 'Survey',   color: 0x0ea5e9, size: 0.068 },
  { label: 'Slides',   color: 0xc4b5fd, size: 0.075 },
  { label: 'Data',     color: 0x7c3aed, size: 0.080 },
  { label: 'Guide',    color: 0xa78bfa, size: 0.073 },
];

export default function ConstellationDome({ width = 520, height = 420 }) {
  const mountRef = useRef(null);

  useEffect(() => {
    const el = mountRef.current;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(52, width / height, 0.1, 100);
    camera.position.set(0, 1.0, 6.5);
    camera.lookAt(0, 0.5, 0);

    scene.add(new THREE.AmbientLight(0xffffff, 0.3));
    const pLight = new THREE.PointLight(0x7c3aed, 2.5, 12);
    pLight.position.set(0, 3, 3);
    scene.add(pLight);

    // ── Central knowledge sphere ──────────────────────────────────────
    const coreMat = new THREE.MeshStandardMaterial({
      color:    0x6d28d9,
      emissive: 0x7c3aed,
      emissiveIntensity: 0.8,
      roughness: 0.2,
      metalness: 0.8,
    });
    const centerSphere = new THREE.Mesh(
      new THREE.SphereGeometry(0.32, 24, 24), coreMat
    );
    scene.add(centerSphere);

    // ── Dome base ring ───────────────────────────────────────────────
    const ringGeo = new THREE.TorusGeometry(2.3, 0.008, 6, 100);
    const ringMat = new THREE.MeshBasicMaterial({
      color:0x7c3aed, transparent:true, opacity:0.20
    });
    scene.add(new THREE.Mesh(ringGeo, ringMat));

    // ── Generate node positions on hemisphere ────────────────────────
    // Use a deterministic distribution across the upper hemisphere
    const nodePositions3D = DOME_NODES.map((_, i) => {
      // Use Fibonacci sphere sampling for even distribution
      const goldenAngle = Math.PI * (3 - Math.sqrt(5));
      const t    = (i + 0.5) / DOME_NODES.length;
      const inc  = Math.acos(1 - t);          // 0 = top, PI/2 = equator
      const az   = goldenAngle * i;
      const R    = 2.25;
      return new THREE.Vector3(
        R * Math.sin(inc) * Math.cos(az),
        R * Math.cos(inc),                    // y is up
        R * Math.sin(inc) * Math.sin(az)
      );
    });

    // ── Create node spheres ──────────────────────────────────────────
    DOME_NODES.forEach((node, i) => {
      const nodeMat = new THREE.MeshStandardMaterial({
        color:    node.color,
        emissive: node.color,
        emissiveIntensity: 0.5,
        roughness: 0.3,
        metalness: 0.7,
      });
      const nodeMesh = new THREE.Mesh(
        new THREE.SphereGeometry(node.size, 10, 10), nodeMat
      );
      nodeMesh.position.copy(nodePositions3D[i]);
      scene.add(nodeMesh);

      // Line from node to center
      const lineGeo       = new THREE.BufferGeometry();
      const linePositions = new Float32Array([
        nodePositions3D[i].x, nodePositions3D[i].y, nodePositions3D[i].z,
        0, 0, 0
      ]);
      lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
      const lineMat = new THREE.LineBasicMaterial({
        color: node.color, transparent: true, opacity: 0.12
      });
      scene.add(new THREE.Line(lineGeo, lineMat));
    });

    // ── Constellation edges (between nearby nodes) ────────────────────
    const CONNECTION_DIST = 1.4;
    const edgeMat = new THREE.LineBasicMaterial({
      color: 0x7c3aed, transparent: true, opacity: 0.18
    });

    for (let a = 0; a < DOME_NODES.length; a++) {
      for (let b = a + 1; b < DOME_NODES.length; b++) {
        if (nodePositions3D[a].distanceTo(nodePositions3D[b]) < CONNECTION_DIST) {
          const geo = new THREE.BufferGeometry().setFromPoints([
            nodePositions3D[a], nodePositions3D[b]
          ]);
          scene.add(new THREE.Line(geo, edgeMat));
        }
      }
    }

    // ── The dome: a wireframe hemisphere shell ────────────────────────
    const domeGeo = new THREE.SphereGeometry(2.35, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
    const domeMat = new THREE.MeshBasicMaterial({
      color: 0x7c3aed, wireframe: true, transparent: true, opacity: 0.05
    });
    scene.add(new THREE.Mesh(domeGeo, domeMat));

    // ── Animation ────────────────────────────────────────────────────
    let animId, time = 0;
    const domeGroup = new THREE.Group();
    scene.children.forEach(c => {
      if (c !== pLight && !(c instanceof THREE.AmbientLight)) {
        scene.remove(c);
        domeGroup.add(c);
      }
    });
    scene.add(domeGroup);

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time  += 0.004;

      domeGroup.rotation.y += 0.003;   // Slow continuous rotation

      // Core pulse
      const p = 1 + Math.sin(time * 2) * 0.07;
      centerSphere.scale.setScalar(p);
      coreMat.emissiveIntensity = 0.8 + Math.sin(time * 2) * 0.25;

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, [width, height]);

  return (
    <div
      ref={mountRef}
      style={{
        width, height,
        filter: 'drop-shadow(0 0 40px rgba(124,58,237,0.16))',
      }}
    />
  );
}
