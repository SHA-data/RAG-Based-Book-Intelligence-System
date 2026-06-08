import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// 1. Hero Book Model (Page 1)
export function BookModel(props) {
  const bookRef = useRef();

  useFrame((state) => {
    if (bookRef.current) {
      bookRef.current.rotation.y = state.clock.getElapsedTime() * 0.4;
      bookRef.current.rotation.x = Math.sin(state.clock.getElapsedTime() * 0.5) * 0.1;
      bookRef.current.position.y = props.position[1] + Math.sin(state.clock.getElapsedTime()) * 0.15;
    }
  });

  return (
    <group ref={bookRef} {...props} rotation={[0.2, -0.5, 0]}>
      {/* Front Cover */}
      <mesh position={[0, 0, 0.16]} castShadow receiveShadow>
        <boxGeometry args={[2.5, 3.5, 0.08]} />
        <meshStandardMaterial color="#00bcff" roughness={0.3} metalness={0.5} />
      </mesh>

      {/* Back Cover */}
      <mesh position={[0, 0, -0.16]} castShadow receiveShadow>
        <boxGeometry args={[2.5, 3.5, 0.08]} />
        <meshStandardMaterial color="#00bcff" roughness={0.3} metalness={0.5} />
      </mesh>

      {/* Spine */}
      <mesh position={[-1.25, 0, 0]} castShadow>
        <boxGeometry args={[0.08, 3.5, 0.4]} />
        <meshStandardMaterial color="#7f00ff" roughness={0.4} />
      </mesh>

      {/* Pages Block */}
      <mesh position={[0.05, 0, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.36, 3.4, 0.3]} />
        <meshStandardMaterial color="#ffffff" roughness={0.9} />
      </mesh>

      {/* Cyan & Violet stripes on cover */}
      <mesh position={[0, 1, 0.21]}>
        <boxGeometry args={[2.0, 0.05, 0.02]} />
        <meshStandardMaterial color="#00f2fe" metalness={0.8} roughness={0.2} />
      </mesh>
      <mesh position={[0, -1, 0.21]}>
        <boxGeometry args={[2.0, 0.05, 0.02]} />
        <meshStandardMaterial color="#7f00ff" metalness={0.8} roughness={0.2} />
      </mesh>
    </group>
  );
}

// 2. Ingest Scanner Model (Page 2)
export function IngestModel(props) {
  const groupRef = useRef();
  const laserRef = useRef();
  
  // Floating data nodes rising up during scan
  const particles = useMemo(() => {
    return Array.from({ length: 10 }).map((_, i) => ({
      speed: 0.6 + Math.random() * 0.9,
      offset: Math.random() * Math.PI * 2,
      scale: 0.08 + Math.random() * 0.12,
      x: (Math.random() - 0.5) * 2.2,
      z: (Math.random() - 0.5) * 1.2,
    }));
  }, []);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (groupRef.current) {
      groupRef.current.rotation.y = time * 0.15;
    }
    if (laserRef.current) {
      // Sweeping scanner beam moving up and down
      laserRef.current.position.y = Math.sin(time * 2.5) * 1.25;
    }
  });

  return (
    <group ref={groupRef} {...props}>
      {/* Open Book Base */}
      <group position={[0, -0.2, 0]} rotation={[0.4, 0, 0.1]}>
        {/* Left Cover & Page */}
        <mesh position={[-0.8, 0, 0]} rotation={[0, 0.25, 0]} castShadow>
          <boxGeometry args={[1.5, 2.4, 0.08]} />
          <meshStandardMaterial color="#06070d" roughness={0.5} />
        </mesh>
        <mesh position={[-0.8, 0.02, 0.03]} rotation={[0, 0.25, 0]}>
          <boxGeometry args={[1.4, 2.3, 0.05]} />
          <meshStandardMaterial color="#ffffff" roughness={0.8} />
        </mesh>

        {/* Right Cover & Page */}
        <mesh position={[0.8, 0, 0]} rotation={[0, -0.25, 0]} castShadow>
          <boxGeometry args={[1.5, 2.4, 0.08]} />
          <meshStandardMaterial color="#06070d" roughness={0.5} />
        </mesh>
        <mesh position={[0.8, 0.02, 0.03]} rotation={[0, -0.25, 0]}>
          <boxGeometry args={[1.4, 2.3, 0.05]} />
          <meshStandardMaterial color="#ffffff" roughness={0.8} />
        </mesh>

        {/* Spine */}
        <mesh position={[0, -0.01, -0.05]}>
          <boxGeometry args={[0.15, 2.4, 0.15]} />
          <meshStandardMaterial color="#7f00ff" roughness={0.3} />
        </mesh>
      </group>

      {/* Holographic Scanner Beam (moves up/down) */}
      <group ref={laserRef} position={[0, 0, 0.15]}>
        <mesh>
          <boxGeometry args={[3.2, 0.05, 0.05]} />
          <meshStandardMaterial 
            color="#00f2fe" 
            emissive="#00f2fe" 
            emissiveIntensity={2.5} 
            transparent 
            opacity={0.9} 
          />
        </mesh>
        {/* Under-glow plane representing scanner light */}
        <mesh position={[0, -0.2, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <planeGeometry args={[3.0, 0.4]} />
          <meshStandardMaterial 
            color="#00f2fe" 
            emissive="#00f2fe" 
            emissiveIntensity={1.5} 
            transparent 
            opacity={0.35} 
            side={THREE.DoubleSide} 
          />
        </mesh>
      </group>

      {/* Floating particles rising out of book */}
      {particles.map((p, i) => (
        <IngestParticle key={i} particle={p} />
      ))}
    </group>
  );
}

function IngestParticle({ particle }) {
  const ref = useRef();
  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (ref.current) {
      // Float from the book upwards
      const y = ((time * particle.speed) % 3) - 1.0;
      ref.current.position.y = y;
      ref.current.position.x = particle.x + Math.sin(time * 2 + particle.offset) * 0.15;
      ref.current.position.z = particle.z + Math.cos(time * 2 + particle.offset) * 0.15;
      // Shrink as it rises
      const currentScale = particle.scale * (1.0 - (y + 1.0) / 3.0);
      ref.current.scale.setScalar(currentScale > 0 ? currentScale : 0);
    }
  });

  return (
    <mesh ref={ref}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial 
        color="#00f2fe" 
        emissive="#00f2fe" 
        emissiveIntensity={1.0} 
        transparent 
        opacity={0.8} 
      />
    </mesh>
  );
}

// 3. Oracle Quantum Torus Model (Page 3)
export function OracleModel(props) {
  const coreRef = useRef();
  const outerRingRef = useRef();
  const innerRingRef = useRef();
  const satellitesRef = useRef();

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (coreRef.current) {
      // Twist and turn the quantum knot
      coreRef.current.rotation.x = time * 0.35;
      coreRef.current.rotation.y = time * 0.5;
      coreRef.current.rotation.z = Math.sin(time * 0.4) * 0.25;
    }
    if (outerRingRef.current) {
      outerRingRef.current.rotation.y = -time * 0.25;
      outerRingRef.current.rotation.z = time * 0.1;
    }
    if (innerRingRef.current) {
      innerRingRef.current.rotation.x = time * 0.4;
      innerRingRef.current.rotation.y = time * 0.3;
    }
    if (satellitesRef.current) {
      satellitesRef.current.rotation.y = time * 0.6;
    }
  });

  return (
    <group {...props}>
      {/* Core Model: Quantum Torus Knot (Highly smoothed geometry with 256 x 32 segments) */}
      <mesh ref={coreRef} castShadow>
        <torusKnotGeometry args={[0.75, 0.22, 256, 32, 3, 4]} />
        <meshStandardMaterial 
          color="#7f00ff" 
          emissive="#00f2fe" 
          emissiveIntensity={0.8} 
          roughness={0.05} 
          metalness={0.95} 
        />
      </mesh>

      {/* Wireframe overlay to emphasize quantum/computational logic */}
      <mesh ref={coreRef} scale={1.03}>
        <torusKnotGeometry args={[0.75, 0.22, 256, 32, 3, 4]} />
        <meshStandardMaterial 
          color="#00f2fe" 
          wireframe 
          transparent 
          opacity={0.3} 
        />
      </mesh>

      {/* Gyroscopic Inner Ring (Smoothed to 32 x 120 segments) */}
      <mesh ref={innerRingRef}>
        <torusGeometry args={[1.5, 0.03, 32, 120]} />
        <meshStandardMaterial color="#00f2fe" emissive="#00f2fe" emissiveIntensity={1.2} roughness={0.1} />
      </mesh>

      {/* Gyroscopic Outer Ring (Smoothed to 32 x 120 segments) */}
      <mesh ref={outerRingRef} rotation={[Math.PI / 3, Math.PI / 4, 0]}>
        <torusGeometry args={[1.9, 0.02, 32, 120]} />
        <meshStandardMaterial color="#7f00ff" emissive="#7f00ff" emissiveIntensity={0.8} roughness={0.1} />
      </mesh>

      {/* Orbiting Satellite Data Nodes (High segments for perfect spheres) */}
      <group ref={satellitesRef}>
        <mesh position={[2.3, 0, 0]} scale={0.12}>
          <sphereGeometry args={[1, 32, 32]} />
          <meshStandardMaterial color="#00f2fe" emissive="#00f2fe" emissiveIntensity={1.5} />
        </mesh>
        <mesh position={[-2.3, 0, 0]} scale={0.12}>
          <sphereGeometry args={[1, 32, 32]} />

          <meshStandardMaterial color="#00f2fe" emissive="#00f2fe" emissiveIntensity={1.5} />
        </mesh>
        <mesh position={[0, 0, 2.3]} scale={0.08}>
          <sphereGeometry args={[1, 16, 16]} />
          <meshStandardMaterial color="#7f00ff" emissive="#7f00ff" emissiveIntensity={1.2} />
        </mesh>
        <mesh position={[0, 0, -2.3]} scale={0.08}>
          <sphereGeometry args={[1, 16, 16]} />
          <meshStandardMaterial color="#7f00ff" emissive="#7f00ff" emissiveIntensity={1.2} />
        </mesh>
      </group>
    </group>
  );
}


// 4. Library Stack (Page 4)
export function LibraryModel(props) {
  const groupRef = useRef();

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (groupRef.current) {
      groupRef.current.rotation.y = time * 0.2;
    }
  });

  return (
    <group ref={groupRef} {...props}>
      {/* Stack of 3 books lying on top of each other */}
      <group position={[0, -0.6, 0]} rotation={[0, 0.2, 0]}>
        <BookMesh color="#7f00ff" />
      </group>
      <group position={[0.2, 0, 0.1]} rotation={[0, -0.4, 0]}>
        <BookMesh color="#00f2fe" />
      </group>
      <group position={[-0.1, 0.6, -0.05]} rotation={[0, 0.5, 0]}>
        <BookMesh color="#00bcff" />
      </group>
    </group>
  );
}

function BookMesh({ color }) {
  return (
    <group scale={0.7}>
      <mesh position={[0, 0, 0.16]} castShadow receiveShadow>
        <boxGeometry args={[2.5, 3.5, 0.08]} />
        <meshStandardMaterial color={color} roughness={0.3} metalness={0.4} />
      </mesh>
      <mesh position={[0, 0, -0.16]} castShadow receiveShadow>
        <boxGeometry args={[2.5, 3.5, 0.08]} />
        <meshStandardMaterial color={color} roughness={0.3} metalness={0.4} />
      </mesh>
      <mesh position={[-1.25, 0, 0]} castShadow>
        <boxGeometry args={[0.08, 3.5, 0.4]} />
        <meshStandardMaterial color="#06070d" roughness={0.4} />
      </mesh>
      <mesh position={[0.05, 0, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.36, 3.4, 0.3]} />
        <meshStandardMaterial color="#ffffff" roughness={0.9} />
      </mesh>
    </group>
  );
}
