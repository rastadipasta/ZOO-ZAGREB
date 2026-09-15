'use client';
import { Suspense, useEffect, useRef, useState, useMemo } from 'react';
import { Canvas, useThree, useFrame } from '@react-three/fiber';
import { Html, OrbitControls, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import Icon from './icons';
import { categories, type Place } from '../lib/places';
export type MapAction = {type:'home'|'in'|'out'|'north'|'focus';point?:number[];seq:number};
export type Position = { point:[number,number]; accuracy:number; timestamp:number; inside:boolean };
type Props = {places:Place[]; selected:string|null; onSelect:(p:Place)=>void; action:MapAction; position:Position|null; onReady:()=>void; low:boolean; onHeading:(value:number)=>void};
const ZOO_MODEL_URL='/models/zoo-zagreb.glb?rev=chibi-v1';
function Model({onReady}:{onReady:()=>void}) {
  const {scene} = useGLTF(ZOO_MODEL_URL,'/draco/');
  useEffect(()=>{scene.traverse(o=>{if(o instanceof THREE.Mesh){o.receiveShadow=true;o.castShadow=true;}});onReady();},[scene,onReady]);
  return <primitive object={scene}/>;
}
function Controls({action,onHeading}:{action:MapAction;onHeading:(v:number)=>void}) {
  const controls = useRef<OrbitControlsImpl>(null);const {camera,size,invalidate}=useThree();
  const goal=useRef<{target:THREE.Vector3;position:THREE.Vector3;zoom:number}|null>(null);
  const homeX=size.width<600?-280:-50,homeY=size.width<600?680:600; const fit=Math.min(size.width/(size.width<600?440:550),size.height/445)*.97;
  useEffect(()=>{camera.position.set(homeX,homeY,560);camera.zoom=fit;camera.updateProjectionMatrix();controls.current?.target.set(60,0,-40);controls.current?.update();invalidate();},[size.width,size.height,camera,fit,homeX,homeY,invalidate]);
  useEffect(()=>{
    const c=controls.current;if(!c)return;const target=c.target.clone(),position=camera.position.clone();let zoom=camera.zoom;
    if(action.type==='home'){target.set(60,0,-40);position.set(homeX,homeY,560);zoom=fit;}
    if(action.type==='in')zoom=Math.min(zoom*1.5,12);if(action.type==='out')zoom=Math.max(zoom/1.5,fit*.65);
    if(action.type==='north')position.set(target.x,480+target.y,600+target.z);
    if(action.type==='focus'&&action.point){const next=new THREE.Vector3(action.point[0],0,-action.point[1]);position.add(next.clone().sub(target));target.copy(next);zoom=Math.max(zoom,Math.min(4,fit*2.2));}
    goal.current={target,position,zoom};invalidate();
  },[action,camera,fit,homeX,homeY,invalidate]);
  useFrame((_,dt)=>{const g=goal.current,c=controls.current;if(!g||!c)return;const alpha=window.matchMedia('(prefers-reduced-motion: reduce)').matches?1:1-Math.exp(-dt*9);c.target.lerp(g.target,alpha);camera.position.lerp(g.position,alpha);camera.zoom=THREE.MathUtils.lerp(camera.zoom,g.zoom,alpha);camera.updateProjectionMatrix();c.update();if(camera.position.distanceTo(g.position)<.03&&Math.abs(camera.zoom-g.zoom)<.002)goal.current=null;invalidate();});
  return <OrbitControls ref={controls} makeDefault enableDamping dampingFactor={.12} minZoom={fit*.6} maxZoom={12} minPolarAngle={.2} maxPolarAngle={Math.PI/2.6} enablePan screenSpacePanning={false} onStart={()=>{goal.current=null;}} onChange={()=>{const c=controls.current;if(!c)return;c.target.x=THREE.MathUtils.clamp(c.target.x,-260,370);c.target.z=THREE.MathUtils.clamp(c.target.z,-290,190);onHeading(c.getAzimuthalAngle()*180/Math.PI);}}/>;
}
function Markers({places,selected,onSelect}:Pick<Props,'places'|'selected'|'onSelect'>) {
  const {camera,size}=useThree();const [visible,setVisible]=useState<string[]>([]);const last=useRef('');
  const ordered=useMemo(()=>[...places].sort((a,b)=>(Number(b.id===selected)-Number(a.id===selected))*100+Number(!!b.featured)-Number(!!a.featured)),[places,selected]);
  useFrame(()=>{const occupied:number[][]=[],ids:string[]=[];for(const p of ordered){const v=new THREE.Vector3(p.point[0],10,-p.point[1]).project(camera);const x=(v.x+1)*size.width/2,y=(1-v.y)*size.height/2;if(v.z>1||v.z< -1||x<12||x>size.width-12||y<30||y>size.height-35)continue;if(occupied.some(q=>Math.abs(q[0]-x)<43&&Math.abs(q[1]-y)<51))continue;occupied.push([x,y]);ids.push(p.id);}const key=ids.join(',');if(key!==last.current){last.current=key;setVisible(ids);}});
  return <>{places.filter(p=>visible.includes(p.id)).map(p=><Html key={p.id} position={[p.point[0],10,-p.point[1]]} center zIndexRange={[30,10]}><button className={'map-pin '+(p.id===selected?'selected':'')} style={{'--pin':categories.find(c=>c.id===p.category)?.color} as React.CSSProperties} aria-label={p.name} aria-pressed={p.id===selected} onClick={()=>onSelect(p)}><Icon name={p.icon} size={20}/><span className="pin-label">{p.name}</span></button></Html>)}</>;
}
function MyPosition({position:p}:{position:Position}) {return <group position={[p.point[0],1,-p.point[1]]}><mesh rotation={[-Math.PI/2,0,0]}><circleGeometry args={[Math.min(p.accuracy,250),64]}/><meshBasicMaterial color="#2389ea" transparent opacity={.13} depthWrite={false}/></mesh><Html position={[0,3,0]} center zIndexRange={[40,35]}><div className="location-dot" role="img" aria-label={`Tvoja lokacija, preciznost ${Math.round(p.accuracy)} metara`}/></Html></group>;}
export default function ZooScene(props:Props) {return <Canvas orthographic shadows={props.low?false:"percentage"} frameloop="demand" dpr={props.low?1:[1,1.5]} camera={{position:[60,480,560],near:.1,far:2500,zoom:1}} gl={{antialias:true,alpha:true,powerPreference:'high-performance'}} onCreated={({gl})=>{gl.setClearColor('#eaf0e5',0);gl.toneMapping=THREE.ACESFilmicToneMapping;gl.toneMappingExposure=1.12;}}><ambientLight intensity={1.15}/><hemisphereLight args={['#f8f4df','#657352',1.4]}/><directionalLight position={[-150,400,200]} intensity={2.5} castShadow={!props.low} shadow-mapSize={props.low?[512,512]:[2048,2048]} shadow-camera-left={-450} shadow-camera-right={450} shadow-camera-top={450} shadow-camera-bottom={-450} shadow-camera-near={1} shadow-camera-far={1000} shadow-bias={-.001} shadow-normalBias={.15}/><Suspense fallback={null}><Model onReady={props.onReady}/><Markers places={props.places} selected={props.selected} onSelect={props.onSelect}/>{props.position?.inside&&<MyPosition position={props.position}/>}</Suspense><Controls action={props.action} onHeading={props.onHeading}/></Canvas>;}



