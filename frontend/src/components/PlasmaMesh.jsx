import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function PlasmaMesh() {
  const mountRef = useRef(null);

  useEffect(() => {
    const el = mountRef.current;
    const W  = window.innerWidth;
    const H  = window.innerHeight;

    // ── Renderer ─────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true });
    renderer.setPixelRatio(1);          // Fix at 1× for performance
    renderer.setSize(W, H);
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);

    // ── Scene & camera ───────────────────────────────────────────────
    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(55, W / H, 1, 3000);
    camera.position.set(0, 320, 600);
    camera.lookAt(0, -40, 0);

    // ── Plasma mesh geometry ─────────────────────────────────────────
    // 64×64 subdivisions = 4225 vertices — enough detail, not too heavy
    const geo = new THREE.PlaneGeometry(1400, 1400, 64, 64);
    geo.rotateX(-Math.PI * 0.28);   // Tilt: looks like a surface receding

    const mat = new THREE.MeshBasicMaterial({
      color:       0x7c3aed,
      wireframe:   true,
      transparent: true,
      opacity:     0.13,
    });

    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.y = -180;
    scene.add(mesh);

    // Second layer — slightly larger, slower, lower opacity
    const geo2 = new THREE.PlaneGeometry(1800, 1800, 48, 48);
    geo2.rotateX(-Math.PI * 0.28);
    const mat2 = new THREE.MeshBasicMaterial({
      color:       0x6d28d9,
      wireframe:   true,
      transparent: true,
      opacity:     0.055,
    });
    const mesh2 = new THREE.Mesh(geo2, mat2);
    mesh2.position.y = -220;
    scene.add(mesh2);

    // ── Store original Y positions ───────────────────────────────────
    // We animate Y from the original flat positions
    const pos1 = geo.attributes.position;
    const pos2 = geo2.attributes.position;
    const origY1 = Float32Array.from({ length: pos1.count }, (_, i) => pos1.getY(i));
    const origY2 = Float32Array.from({ length: pos2.count }, (_, i) => pos2.getY(i));

    // ── Mouse parallax ───────────────────────────────────────────────
    const mouse = { x: 0, y: 0 };
    const onMouse = (e) => {
      mouse.x = (e.clientX / window.innerWidth)  * 2 - 1;
      mouse.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener('mousemove', onMouse);

    // ── Animation ────────────────────────────────────────────────────
    let animId;
    let time = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time  += 0.004;     // Slow, breathing speed

      // Animate layer 1
      for (let i = 0; i < pos1.count; i++) {
        const x = pos1.getX(i);
        const z = pos1.getZ(i);
        pos1.setY(i,
          origY1[i] +
          Math.sin(x * 0.007 + time)           * 26 +
          Math.sin(z * 0.005 + time * 1.3)     * 20 +
          Math.sin((x + z) * 0.004 + time * 0.6) * 14 +
          Math.cos(x * 0.011 - time * 0.9)     * 9
        );
      }
      pos1.needsUpdate = true;

      // Animate layer 2 (different phase, slower)
      for (let i = 0; i < pos2.count; i++) {
        const x = pos2.getX(i);
        const z = pos2.getZ(i);
        pos2.setY(i,
          origY2[i] +
          Math.sin(x * 0.005 + time * 0.7)      * 18 +
          Math.sin(z * 0.004 + time * 0.9)      * 14 +
          Math.cos((x - z) * 0.003 + time * 0.5) * 10
        );
      }
      pos2.needsUpdate = true;

      // Subtle camera drift on mouse
      camera.position.x += (mouse.x * 35 - camera.position.x) * 0.025;
      camera.position.y += (-mouse.y * 20 + 320 - camera.position.y) * 0.025;
      camera.lookAt(0, -40, 0);

      renderer.render(scene, camera);
    };
    animate();

    // ── Resize ───────────────────────────────────────────────────────
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', onMouse);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      style={{ position:'fixed', inset:0, zIndex:0, pointerEvents:'none' }}
    />
  );
}
