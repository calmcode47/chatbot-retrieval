import { useEffect, useRef } from 'react';
import * as THREE from 'three';

const NODE_COUNT        = 60;
const CONNECTION_RADIUS = 280;   // max distance for edge creation
const BOUNDS            = 400;   // ±x,y,z boundary for node drift
const DRIFT_SPEED       = 0.12;  // base drift multiplier

export default function ThreeBackground() {
  const mountRef = useRef(null);

  useEffect(() => {
    const el     = mountRef.current;
    const W      = window.innerWidth;
    const H      = window.innerHeight;
    const mouse  = { x: 0, y: 0 };

    // ── Renderer ─────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    // ── Scene + Camera ───────────────────────────────────────────────
    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, W / H, 1, 2000);
    camera.position.z = 700;

    // ── Nodes ────────────────────────────────────────────────────────
    // Each node: {position, velocity}
    const nodes = Array.from({ length: NODE_COUNT }, () => ({
      position: new THREE.Vector3(
        (Math.random() - 0.5) * BOUNDS * 2,
        (Math.random() - 0.5) * BOUNDS * 2,
        (Math.random() - 0.5) * BOUNDS * 1.2
      ),
      velocity: new THREE.Vector3(
        (Math.random() - 0.5) * DRIFT_SPEED,
        (Math.random() - 0.5) * DRIFT_SPEED,
        (Math.random() - 0.5) * DRIFT_SPEED * 0.4
      ),
    }));

    // Points geometry for nodes
    const nodePositions = new Float32Array(NODE_COUNT * 3);
    nodes.forEach((n, i) => {
      nodePositions[i * 3]     = n.position.x;
      nodePositions[i * 3 + 1] = n.position.y;
      nodePositions[i * 3 + 2] = n.position.z;
    });

    const nodeGeom = new THREE.BufferGeometry();
    nodeGeom.setAttribute('position', new THREE.BufferAttribute(nodePositions, 3));

    const nodeMat = new THREE.PointsMaterial({
      color:        0xf59e0b,   // amber
      size:         2.5,
      transparent:  true,
      opacity:      0.22,
      sizeAttenuation: true,
    });

    const nodesMesh = new THREE.Points(nodeGeom, nodeMat);
    scene.add(nodesMesh);

    // ── Edges (lines between nearby nodes) ───────────────────────────
    // Max possible edges: N*(N-1)/2 = 1770 for 60 nodes
    // Pre-allocate a fixed buffer and update dynamically
    const MAX_EDGES = 1200;
    const edgePositions = new Float32Array(MAX_EDGES * 2 * 3);  // 2 vertices per edge

    const edgeGeom = new THREE.BufferGeometry();
    edgeGeom.setAttribute('position', new THREE.BufferAttribute(edgePositions, 3));
    edgeGeom.setDrawRange(0, 0);

    const edgeMat = new THREE.LineBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.16 });

    const edgesMesh = new THREE.LineSegments(edgeGeom, edgeMat);
    scene.add(edgesMesh);

    // ── Animation ────────────────────────────────────────────────────
    let animId;
    let edgeCount = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);

      // Update node positions
      nodes.forEach((n, i) => {
        n.position.addScaledVector(n.velocity, 1);

        // Reverse at bounds
        if (Math.abs(n.position.x) > BOUNDS) n.velocity.x *= -1;
        if (Math.abs(n.position.y) > BOUNDS) n.velocity.y *= -1;
        if (Math.abs(n.position.z) > BOUNDS * 0.6) n.velocity.z *= -1;

        nodePositions[i * 3]     = n.position.x;
        nodePositions[i * 3 + 1] = n.position.y;
        nodePositions[i * 3 + 2] = n.position.z;
      });
      nodeGeom.attributes.position.needsUpdate = true;

      // Rebuild edges
      edgeCount = 0;
      for (let a = 0; a < nodes.length && edgeCount < MAX_EDGES; a++) {
        for (let b = a + 1; b < nodes.length && edgeCount < MAX_EDGES; b++) {
          const dist = nodes[a].position.distanceTo(nodes[b].position);
          if (dist < CONNECTION_RADIUS) {
            const idx = edgeCount * 6;
            edgePositions[idx]     = nodes[a].position.x;
            edgePositions[idx + 1] = nodes[a].position.y;
            edgePositions[idx + 2] = nodes[a].position.z;
            edgePositions[idx + 3] = nodes[b].position.x;
            edgePositions[idx + 4] = nodes[b].position.y;
            edgePositions[idx + 5] = nodes[b].position.z;
            edgeCount++;
          }
        }
      }
      edgeGeom.attributes.position.needsUpdate = true;
      edgeGeom.setDrawRange(0, edgeCount * 2);

      // Mouse parallax — subtle camera tilt
      camera.position.x += (mouse.x * 60 - camera.position.x) * 0.02;
      camera.position.y += (-mouse.y * 40 - camera.position.y) * 0.02;
      camera.lookAt(scene.position);

      renderer.render(scene, camera);
    };
    animate();

    // ── Mouse tracking ───────────────────────────────────────────────
    const onMouseMove = (e) => {
      mouse.x = (e.clientX / window.innerWidth)  * 2 - 1;
      mouse.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener('mousemove', onMouseMove);

    // ── Resize ───────────────────────────────────────────────────────
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
        inset:    0,
        zIndex:   0,
        pointerEvents: 'none',
      }}
    />
  );
}
