import React, { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useScroll } from '@react-three/drei';
import * as THREE from 'three';

export default function BookModel() {
  const scroll = useScroll();
  const bookRef = useRef();

  useFrame((state, delta) => {
    const offset = scroll.offset;
    
    if (bookRef.current) {
      // Rotate the book as the user scrolls
      bookRef.current.rotation.y = THREE.MathUtils.lerp(
        bookRef.current.rotation.y,
        offset * Math.PI * 2,
        0.1
      );

      // Move the book vertically/horizontally based on scroll
      bookRef.current.position.y = THREE.MathUtils.lerp(
        bookRef.current.position.y,
        Math.sin(offset * Math.PI) * 2 - 1,
        0.1
      );
      
      // Floating animation effect
      bookRef.current.position.y += Math.sin(state.clock.elapsedTime) * 0.05;
    }
  });

  return (
    <group ref={bookRef} position={[2, 0, 0]} rotation={[0.2, -0.5, 0]}>
      {/* Front Cover */}
      <mesh position={[0, 0, 0.16]} castShadow receiveShadow>
        <boxGeometry args={[2.5, 3.5, 0.08]} />
        <meshStandardMaterial color="#4f46e5" roughness={0.3} metalness={0.2} />
      </mesh>

      {/* Back Cover */}
      <mesh position={[0, 0, -0.16]} castShadow receiveShadow>
        <boxGeometry args={[2.5, 3.5, 0.08]} />
        <meshStandardMaterial color="#4f46e5" roughness={0.3} metalness={0.2} />
      </mesh>

      {/* Spine */}
      <mesh position={[-1.25, 0, 0]} rotation={[0, 0, 0]} castShadow>
        <boxGeometry args={[0.08, 3.5, 0.4]} />
        <meshStandardMaterial color="#312e81" roughness={0.4} />
      </mesh>

      {/* Pages Block */}
      <mesh position={[0.05, 0, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.36, 3.4, 0.3]} />
        <meshStandardMaterial color="#fdfbf7" roughness={0.9} />
      </mesh>

      {/* Gold details / stripes on cover to make it look premium */}
      <mesh position={[0, 1, 0.21]}>
        <boxGeometry args={[2.0, 0.05, 0.02]} />
        <meshStandardMaterial color="#fbbf24" metalness={0.8} roughness={0.2} />
      </mesh>
      <mesh position={[0, -1, 0.21]}>
        <boxGeometry args={[2.0, 0.05, 0.02]} />
        <meshStandardMaterial color="#fbbf24" metalness={0.8} roughness={0.2} />
      </mesh>
    </group>
  );
}

