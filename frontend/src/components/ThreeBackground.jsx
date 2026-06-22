import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function ThreeBackground() {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // --- Scene Setup ---
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x030712, 0.008); // Dark Nordic Ice fog

    // --- Camera Setup ---
    const camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      1,
      1000
    );
    camera.position.set(0, 45, 120);
    camera.lookAt(0, 10, 0);

    // --- Renderer Setup ---
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x030712, 1); // Dark background
    containerRef.current.appendChild(renderer.domElement);

    // --- 1. Cyber-Grid Floor ---
    const gridWidth = 400;
    const gridHeight = 400;
    const segmentsX = 30;
    const segmentsY = 30;
    const gridGeom = new THREE.PlaneGeometry(gridWidth, gridHeight, segmentsX, segmentsY);
    gridGeom.rotateX(-Math.PI / 2); // Lay flat

    const wireframe = new THREE.WireframeGeometry(gridGeom);
    const gridMaterial = new THREE.LineBasicMaterial({
      color: 0x1d4ed8, // Cobalt blue
      transparent: true,
      opacity: 0.12,
    });
    const grid = new THREE.LineSegments(wireframe, gridMaterial);
    grid.position.y = -10;
    scene.add(grid);

    // Keep reference to initial grid positions for wave math
    const originalPositions = gridGeom.attributes.position.clone();

    // --- 2. Floating Data Packets (Point Particles) ---
    const particleCount = 100;
    const particleGeom = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = [];

    for (let i = 0; i < particleCount; i++) {
      // Scatter particles above the grid floor
      positions[i * 3] = (Math.random() - 0.5) * 300;
      positions[i * 3 + 1] = Math.random() * 80 - 5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 200;

      velocities.push({
        x: (Math.random() - 0.5) * 0.05,
        y: Math.random() * 0.04 + 0.02, // Drifting upwards
        z: (Math.random() - 0.5) * 0.05,
      });
    }

    particleGeom.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    // Custom circle glowing particle texture (Teal/Indigo blend)
    const canvas = document.createElement("canvas");
    canvas.width = 16;
    canvas.height = 16;
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
    gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
    gradient.addColorStop(0.3, "rgba(45, 212, 191, 0.8)"); // Teal
    gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 16, 16);
    const texture = new THREE.CanvasTexture(canvas);

    const particleMaterial = new THREE.PointsMaterial({
      size: 3.5,
      map: texture,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      transparent: true,
      opacity: 0.6,
    });

    const particles = new THREE.Points(particleGeom, particleMaterial);
    scene.add(particles);

    // --- 3. Interactive Mouse Parallax ---
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    const handleMouseMove = (event) => {
      targetMouseX = (event.clientX - window.innerWidth / 2) * 0.04;
      targetMouseY = (event.clientY - window.innerHeight / 2) * 0.02;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // --- Resize Handler ---
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener("resize", handleResize);

    // --- Animation Loop ---
    let animationFrameId;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();

      // Smooth mouse follow (interpolation)
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Parallax camera rotation
      camera.position.x = mouseX;
      camera.position.y = 45 - mouseY;
      camera.lookAt(0, 15, 0);

      // --- Wavy Grid Animation ---
      const gridPos = grid.geometry.attributes.position.array;
      const origPos = originalPositions.array;

      for (let i = 0; i < gridPos.length / 3; i++) {
        const x = origPos[i * 3];
        const z = origPos[i * 3 + 2];

        // Animate Y position of grid vertices based on mathematical waves
        gridPos[i * 3 + 1] = Math.sin(x * 0.015 + time) * Math.cos(z * 0.015 + time * 0.8) * 8;
      }
      grid.geometry.attributes.position.needsUpdate = true;

      // --- Particle Upward Drift Animation ---
      const partPos = particles.geometry.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        partPos[i * 3] += velocities[i].x;
        partPos[i * 3 + 1] += velocities[i].y;
        partPos[i * 3 + 2] += velocities[i].z;

        // Wrap around boundaries
        if (partPos[i * 3 + 1] > 75) {
          partPos[i * 3 + 1] = -5; // Reset to floor height
          partPos[i * 3] = (Math.random() - 0.5) * 300;
          partPos[i * 3 + 2] = (Math.random() - 0.5) * 200;
        }
      }
      particles.geometry.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // --- Cleanup ---
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      if (renderer && renderer.domElement && containerRef.current) {
        containerRef.current.removeChild(renderer.domElement);
      }
      scene.clear();
    };
  }, []);

  return <div ref={containerRef} className="three-background-canvas" />;
}
