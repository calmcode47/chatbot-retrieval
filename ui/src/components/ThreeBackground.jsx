import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function ThreeBackground() {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // --- Scene Setup ---
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x0a0c10, 0.015);

    // --- Camera Setup ---
    const camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      1,
      1000
    );
    camera.position.z = 100;

    // --- Renderer Setup ---
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x050608, 1); // Dark background
    containerRef.current.appendChild(renderer.domElement);

    // --- Particles (Stars/Constellation) ---
    const particleCount = 150;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = [];

    for (let i = 0; i < particleCount; i++) {
      // Random coordinates in space
      positions[i * 3] = (Math.random() - 0.5) * 300;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 300;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 200;

      // Random velocities
      velocities.push({
        x: (Math.random() - 0.5) * 0.1,
        y: (Math.random() - 0.5) * 0.1,
        z: (Math.random() - 0.5) * 0.1,
      });
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    // Custom circle particle texture (using dynamic canvas instead of loading external assets)
    const canvas = document.createElement("canvas");
    canvas.width = 16;
    canvas.height = 16;
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
    gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
    gradient.addColorStop(0.3, "rgba(103, 132, 255, 0.8)");
    gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 16, 16);
    const texture = new THREE.CanvasTexture(canvas);

    const material = new THREE.PointsMaterial({
      size: 4,
      map: texture,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      transparent: true,
      opacity: 0.8,
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // --- Interactive Mouse Effect ---
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    const handleMouseMove = (event) => {
      targetMouseX = (event.clientX - window.innerWidth / 2) * 0.05;
      targetMouseY = (event.clientY - window.innerHeight / 2) * 0.05;
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

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Smooth mouse follow (interpolation)
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Parallax rotation
      particles.rotation.y = mouseX * 0.002;
      particles.rotation.x = mouseY * 0.002;

      // Update particle positions
      const positionsAttr = particles.geometry.attributes.position.array;
      for (let i = 0; i < particleCount; i++) {
        // Apply velocity
        positionsAttr[i * 3] += velocities[i].x;
        positionsAttr[i * 3 + 1] += velocities[i].y;
        positionsAttr[i * 3 + 2] += velocities[i].z;

        // Boundary checks (wrap around)
        if (Math.abs(positionsAttr[i * 3]) > 180) velocities[i].x *= -1;
        if (Math.abs(positionsAttr[i * 3 + 1]) > 180) velocities[i].y *= -1;
        if (Math.abs(positionsAttr[i * 3 + 2]) > 150) velocities[i].z *= -1;
      }
      particles.geometry.attributes.position.needsUpdate = true;

      // Rotate group gently
      particles.rotation.z += 0.0003;

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
