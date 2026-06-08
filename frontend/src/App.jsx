import React, { Suspense } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { ScrollControls, Scroll, ContactShadows } from '@react-three/drei';
import { BookModel, IngestModel, OracleModel, LibraryModel } from './components/Models';
import UIOverlay from './components/UIOverlay';

function ModelsContainer() {
  const { height } = useThree().viewport;
  return (
    <group>
      <BookModel position={[2.2, 0, 0]} />
      <IngestModel position={[-2.2, -height, 0]} />
      <OracleModel position={[2.2, -height * 2, 0]} />
      <LibraryModel position={[0, -height * 3, 0]} />
    </group>
  );
}

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', background: 'var(--bg-color)' }}>
      <Canvas shadows camera={{ position: [0, 0, 8], fov: 45 }}>
        {/* Lighting */}
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 8, 5]} intensity={1.5} castShadow />
        <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1.5} castShadow />
        <pointLight position={[-10, -10, -10]} intensity={0.8} color="#00f2fe" />
        
        <Suspense fallback={<div>Loading 3D Scene...</div>}>
          {/* We define 4 pages of scrolling */}
          <ScrollControls pages={4} damping={0.25}>
            
            {/* The 3D scene elements */}
            <Scroll>
              <ModelsContainer />
              
              {/* Floor Shadow */}
              <ContactShadows 
                position={[0, -2.5, 0]} 
                opacity={0.5} 
                scale={25} 
                blur={2.5} 
                far={5} 
                color="#00f2fe" 
              />
            </Scroll>
            
            {/* The HTML overlay elements */}
            <Scroll html style={{ width: '100%' }}>
              <UIOverlay />
            </Scroll>
            
          </ScrollControls>
        </Suspense>
      </Canvas>
    </div>
  );
}



export default App;
