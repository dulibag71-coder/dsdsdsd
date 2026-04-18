import React, { useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Line } from '@react-three/drei';

// The "Kinetic Grid" Colors
const ACTION_GREEN = '#9ffb06';
const SURFACE_PRIMARY = '#ffffff';
const SURFACE_CONTAINER_LOWEST = 'transparent'; // Let App.js background bleed through

function Skeleton({ poses, isComparison = false, currentFrameIdx }) {
  if (!poses || poses.length === 0) return null;

  const frameLimit = poses.length;
  const idx = currentFrameIdx % frameLimit;
  const currentKeypoints = typeof poses[idx].keypoints_json === 'string' 
      ? JSON.parse(poses[idx].keypoints_json) 
      : poses[idx];

  const connections = [
    [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], 
    [11, 23], [12, 24], [23, 24],                     
    [23, 25], [25, 27], [24, 26], [26, 28]            
  ];

  // Primary model is energetic white/green, comparison is a ghosted secondary container look
  const modelColor = isComparison ? '#414a34' : SURFACE_PRIMARY;
  const modelOpacity = isComparison ? 0.3 : 1.0;

  return (
    <group position={[0, -0.5, 0]} scale={[2.2, 2.2, 2.2]}>
      {currentKeypoints.map((kp, i) => {
        if (kp.visibility < 0.5) return null;
        return (
          <mesh position={[kp.x, kp.y, kp.z]} key={`kp-${i}`}>
            <sphereGeometry args={[0.02, 16, 16]} />
            <meshStandardMaterial 
                color={isComparison ? ACTION_GREEN : modelColor} 
                opacity={modelOpacity} 
                transparent 
                emissive={isComparison ? ACTION_GREEN : '#444'} 
                emissiveIntensity={isComparison ? 0.2 : 0.5} 
            />
          </mesh>
        );
      })}

      {connections.map(([start, end], i) => {
        const kpStart = currentKeypoints[start];
        const kpEnd = currentKeypoints[end];
        if (!kpStart || !kpEnd || kpStart.visibility < 0.5 || kpEnd.visibility < 0.5) return null;

        const points = [
          [kpStart.x, kpStart.y, kpStart.z],
          [kpEnd.x, kpEnd.y, kpEnd.z]
        ];

        return (
          <Line key={`bone-${i}`} points={points} color={modelColor} lineWidth={isComparison ? 5 : 8} transparent opacity={modelOpacity} />
        );
      })}
    </group>
  );
}

function Trajectory({ poses, currentFrameIdx }) {
  if (!poses || poses.length === 0) return null;

  const leftWristPoints = [];
  const rightWristPoints = [];

  for (let i = 0; i <= currentFrameIdx; i++) {
    const idx = i % poses.length;
    const keypoints = typeof poses[idx].keypoints_json === 'string' 
      ? JSON.parse(poses[idx].keypoints_json) 
      : poses[idx];
    
    if (keypoints[15]) leftWristPoints.push([keypoints[15].x, keypoints[15].y, keypoints[15].z]);
    if (keypoints[16]) rightWristPoints.push([keypoints[16].x, keypoints[16].y, keypoints[16].z]);
  }

  // Trajectory uses ACTION_GREEN to vibrate with functional energy
  return (
    <group position={[0, -0.5, 0]} scale={[2.2, 2.2, 2.2]}>
      {leftWristPoints.length > 1 && <Line points={leftWristPoints} color={ACTION_GREEN} lineWidth={3} />}
      {rightWristPoints.length > 1 && <Line points={rightWristPoints} color={ACTION_GREEN} lineWidth={3} />}
    </group>
  );
}

export default function ThreeViewer({ poses, comparisonPoses }) {
  const [frameIdx, setFrameIdx] = useState(0);

  useFrame(() => {
    if (poses && poses.length > 0) {
      setFrameIdx((prev) => (prev + 1));
    }
  });

  return (
    <Canvas style={{ flex: 1, backgroundColor: SURFACE_CONTAINER_LOWEST }} camera={{ position: [0, 0, 3.5] }}>
      <ambientLight intensity={0.8} />
      <directionalLight position={[0, 10, 10]} intensity={1.5} color="#ffffff" />
      
      <Skeleton poses={poses} currentFrameIdx={frameIdx} />
      <Trajectory poses={poses} currentFrameIdx={frameIdx} />

      {comparisonPoses && comparisonPoses.length > 0 && (
        <Skeleton poses={comparisonPoses} isComparison={true} currentFrameIdx={frameIdx} />
      )}
    </Canvas>
  );
}
