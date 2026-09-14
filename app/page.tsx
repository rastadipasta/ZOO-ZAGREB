'use client';
import { Component, lazy, Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { ArrowDownToLine, ArrowLeft, ArrowUpRight, ChevronDown, ChevronRight, Compass, Crosshair, Leaf, MapPin, Minus, Plus, RotateCcw, SlidersHorizontal, X, Info, LoaderCircle } from 'lucide-react';
import Icon from './icons';
import { categories, places, geography, type Place, type Category } from '../lib/places';
import { locationQuality } from '../lib/geo';
import { locationError, mapPosition } from '../lib/location';
import type { MapAction, Position } from './zoo-scene';
const Scene=lazy(()=>import('./zoo-scene'));
class SceneBoundary extends Component<{children:React.ReactNode;onError:()=>void},{error:boolean}>{
  state={error:false};static getDerivedStateFromError(){return{error:true};}componentDidCatch(){this.props.onError();}
  render(){return this.state.error?<div className="scene-error"><Compass size={38}/><h2>3D prikaz nije dostupan</h2><p>Pokušaj ponovno učitati kartu ili pregledaj nastambe u popisu.</p><button onClick={()=>window.location.reload()}>Ponovno učitaj</button></div>:this.props.children;}
}
type InstallEvent=Event&{prompt:()=>Promise<void>;userChoice:Promise<{outcome:string}>};
export default function Home(){
  const [category,setCategory]=useState<Category|'all'>('all'),[selected,setSelected]=useState<Place|null>(null);
  const [legend,setLegend]=useState(false),[allPlaces,setAllPlaces]=useState(false),[about,setAbout]=useState(false);
  const [ready,setReady]=useState(false),[error,setError]=useState(false),[low,setLow]=useState(false),[heading,setHeading]=useState(0);
  const [position,setPosition]=useState<Position|null>(null),[locating,setLocating]=useState(false),[tracking,setTracking]=useState(false),[locationMessage,setLocationMessage]=useState('');
  const [online,setOnline]=useState(true),[install,setInstall]=useState<InstallEvent|null>(null);
  const [action,setAction]=useState<MapAction>({type:'home',seq:0});
  const watch=useRef<number|null>(null),selectedTrigger=useRef<HTMLElement|null>(null),closeRef=useRef<HTMLButtonElement>(null),selectedRef=useRef<Place|null>(null),panelRef=useRef<HTMLElement|null>(null);
  const doAction=useCallback((type:MapAction['type'],point?:number[])=>setAction(a=>({type,point,seq:a.seq+1})),[]);
  const selectPlace=useCallback((p:Place)=>{selectedTrigger.current=document.activeElement as HTMLElement;setSelected(p);setLegend(false);doAction('focus',p.point);},[doAction]);
  const closePlace=useCallback(()=>{setSelected(null);selectedTrigger.current?.focus();},[]);
  const onReady=useCallback(()=>setReady(true),[]);
  useEffect(()=>{selectedRef.current=selected;if(selected)closeRef.current?.focus();},[selected]);
  useEffect(()=>{
    setLow(window.matchMedia('(max-width: 700px)').matches);setOnline(navigator.onLine);
    const change=()=>setOnline(navigator.onLine),installer=(e:Event)=>{e.preventDefault();setInstall(e as InstallEvent);};
    window.addEventListener('online',change);window.addEventListener('offline',change);window.addEventListener('beforeinstallprompt',installer);
    if('serviceWorker' in navigator&&window.isSecureContext&&process.env.NODE_ENV==='production')navigator.serviceWorker.register('/sw.js').catch(()=>{});
    return()=>{window.removeEventListener('online',change);window.removeEventListener('offline',change);window.removeEventListener('beforeinstallprompt',installer);if(watch.current!==null)navigator.geolocation.clearWatch(watch.current);};
  },[]);
  useEffect(()=>{if(!tracking)return;const timer=window.setInterval(()=>{if(position&&Date.now()-position.timestamp>45000)setLocationMessage('Položaj se neko vrijeme nije osvježio. Zadnja lokacija možda više nije aktualna.');},10000);return()=>window.clearInterval(timer);},[tracking,position]);
  useEffect(()=>{
    const key=(e:KeyboardEvent)=>{if(e.key==='Escape'){if(about)setAbout(false);else if(selected)closePlace();else setLegend(false);}if(e.key==='Tab'&&selected&&panelRef.current){const items=Array.from(panelRef.current.querySelectorAll<HTMLElement>('button,a[href]')),first=items[0],last=items.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}};
    window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key);
  },[about,selected,closePlace]);
  useEffect(()=>{
    const context=(document as Document&{modelContext?:{registerTool:(tool:unknown,options:{signal:AbortSignal})=>void|Promise<void>}}).modelContext;if(!context?.registerTool)return;const lifecycle=new AbortController();
    const tools=[{name:'list_zoo_places',description:'Read the available Zagreb Zoo map locations.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:()=>places.map(p=>({id:p.id,name:p.name,category:p.category}))},{name:'open_zoo_place',description:'Open a location information panel and focus the 3D map.',inputSchema:{type:'object',properties:{id:{type:'string'}},required:['id'],additionalProperties:false},annotations:{readOnlyHint:false},execute:async(input:unknown)=>{if(!input||typeof input!=='object'||!('id' in input)||typeof input.id!=='string')throw new Error('A place id is required.');const p=places.find(p=>p.id===input.id);if(!p)throw new Error('Unknown place id.');flushSync(()=>{setCategory('all');selectPlace(p);});return{id:p.id,name:p.name,opened:selectedRef.current?.id===p.id};}}];
    for(const t of tools){try{Promise.resolve(context.registerTool(t,{signal:lifecycle.signal})).catch(()=>{});}catch{}}return()=>lifecycle.abort();
  },[selectPlace]);
  function locate(){
    if(position&&tracking){if(position.inside)doAction('focus',position.point);return;}
    if(!navigator.geolocation){setLocationMessage('Ovaj preglednik ne podržava prikaz lokacije.');return;}
    if(!window.isSecureContext){setLocationMessage('Za lokaciju otvori aplikaciju putem sigurne HTTPS poveznice.');return;}
    setLocating(true);setLocationMessage('Tražim tvoju lokaciju…');let first=true;
    watch.current=navigator.geolocation.watchPosition(p=>{
      const next=mapPosition(p,geography.boundary),{point,inside}=next;
      setPosition(next);setLocating(false);setTracking(true);setLocationMessage(!inside?'Trenutačno si izvan područja Zoo-a. Kartu možeš slobodno istraživati.':locationQuality(next.accuracy)==='poor'?'GPS signal je slab. Plavi krug pokazuje koliko je položaj približan.':`Lokacija je uključena · preciznost oko ${Math.round(next.accuracy)} m`);
      if(first&&inside)doAction('focus',point);first=false;
    },e=>{setLocating(false);setTracking(false);setPosition(null);setLocationMessage(locationError(e.code));if(watch.current!==null)navigator.geolocation.clearWatch(watch.current);watch.current=null;},{enableHighAccuracy:true,timeout:15000,maximumAge:10000});
  }
  function stopLocation(){if(watch.current!==null)navigator.geolocation.clearWatch(watch.current);watch.current=null;setTracking(false);setPosition(null);setLocationMessage('Prikaz lokacije je isključen.');}
  const filtered=places.filter(p=>category==='all'||p.category===category),listed=allPlaces?filtered:filtered.filter(p=>p.featured||category!=='all').slice(0,8),activeCategory=categories.find(c=>c.id===category)!;
  return <main className="zoo-app">
    <header className="topbar" inert={!!selected||about}><a className="brand" href="/" aria-label="Zoo Zagreb, početna karta"><span className="brand-word">zoo<span className="brand-leaf"><Leaf size={18}/></span></span><span className="brand-city">Zagreb</span></a><div className="header-divider"/><div className="header-title"><h1>Interaktivna karta</h1><span>BLIZU PRIRODI, BLIŽI JEDNI DRUGIMA</span></div><div className="header-right"><span className="preview-badge"><span/>Pregledna verzija</span><button className="round-button info-button" aria-label="O karti i izvorima" onClick={()=>setAbout(true)}><Info size={20}/></button><a className="visit-link" href="https://zoo.hr/" target="_blank" rel="noreferrer">Zoo Zagreb <ArrowUpRight size={17}/></a></div></header>
    <div className="map-workspace" inert={!!selected||about}>
      <aside className={'explorer '+(legend?'mobile-open':'')} aria-label="Legenda i popis lokacija">
        <div className="explorer-heading"><div><p className="eyebrow">DOBRO DOŠLI U MAKSIMIR</p><h2>Istraži Zoo<span>.</span></h2></div><button className="round-button mobile-close" onClick={()=>setLegend(false)} aria-label="Zatvori popis"><X size={18}/></button></div><p className="explorer-description">Odaberi ikonicu i upoznaj svijet koji se krije iza nje.</p>
        <div className="categories" aria-label="Kategorije lokacija">{categories.map(c=><button key={c.id} className={'category '+(category===c.id?'active':'')} onClick={()=>{setCategory(c.id);setAllPlaces(false);}} aria-pressed={category===c.id} style={{'--category':c.color} as React.CSSProperties}><span className="category-icon"><Icon name={c.icon} size={18}/></span><span>{c.name}</span><span className="category-count">{c.id==='all'?places.length:places.filter(p=>p.category===c.id).length}</span></button>)}</div>
        <div className="list-heading"><span>{category==='all'?'ZA POČETAK ISTRAŽIVANJA':activeCategory.name.toLocaleUpperCase('hr')}</span><span>{filtered.length}</span></div><div className="place-list">{listed.map(p=><button key={p.id} className={'place-row '+(selected?.id===p.id?'current':'')} onClick={()=>selectPlace(p)}><Icon name={p.icon} size={17}/><span>{p.name}</span><ChevronRight size={15}/></button>)}</div>
        {!allPlaces&&filtered.length>listed.length&&<button className="all-places" onClick={()=>setAllPlaces(true)}>Prikaži sve lokacije <ChevronDown size={16}/></button>}<div className="explorer-bottom"><Leaf size={18}/><span>Otkrij. Doživi. Čuvaj.</span></div>
      </aside>
      <section className="map-stage" aria-label="Interaktivna 3D karta zoološkog vrta"><div className="map-topline"><span className="view-label"><span className="green-dot"/>3D KARTA <span className="label-divider">/</span> ZAGREB</span><button className="quality-button" onClick={()=>setLow(!low)} aria-pressed={low}><SlidersHorizontal size={15}/>{low?'Lakši prikaz':'Detaljan prikaz'}</button></div>
        <SceneBoundary onError={()=>setError(true)}><Suspense fallback={null}><Scene places={filtered} selected={selected?.id||null} onSelect={selectPlace} action={action} position={position} onReady={onReady} low={low} onHeading={setHeading}/></Suspense></SceneBoundary>
        {!ready&&!error&&<div className="loading-card" role="status"><LoaderCircle className="spin" size={24}/><strong>Ulazimo u mali divlji svijet</strong><span>Učitavanje 3D karte…</span></div>}
        <div className="map-controls"><button className="compass-button" onClick={()=>doAction('north')} aria-label="Okreni kartu prema sjeveru"><span>N</span><Compass size={30} style={{transform:`rotate(${-heading}deg)`}}/></button><div className="zoom-controls"><button aria-label="Približi kartu" onClick={()=>doAction('in')}><Plus size={21}/></button><button aria-label="Udalji kartu" onClick={()=>doAction('out')}><Minus size={21}/></button></div><button className="reset-button" aria-label="Prikaži cijeli Zoo" onClick={()=>doAction('home')}><RotateCcw size={19}/></button></div>
        <div className="map-bottom"><span className="gesture-hint">Povuci za rotaciju <span>·</span> Približi za detalje</span><div className="location-actions"><button className={'locate-button '+(tracking?'tracking':'')} onClick={locate} disabled={locating}>{locating?<LoaderCircle size={18} className="spin"/>:<Crosshair size={19}/>}<span>{tracking?'Moja lokacija':'Pronađi me'}</span></button>{tracking&&<button className="stop-location" aria-label="Isključi praćenje lokacije" onClick={stopLocation}><X size={16}/></button>}</div></div>
        <div className="map-credit"><a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">© OpenStreetMap contributors</a><span>Umjetnički 3D prikaz · položaji nisu terenski potvrđeni</span></div><button className="mobile-legend" onClick={()=>setLegend(true)}><Icon name="map" size={18}/>Istraži lokacije</button>
      </section>
    </div>
    {(locationMessage||!online)&&<div className="status-toast" role="status"><MapPin size={18}/><span>{!online?'Nema interneta. Već preuzeti sadržaji mogu ostati dostupni.':locationMessage}</span><button onClick={()=>setLocationMessage('')} aria-label="Zatvori obavijest"><X size={17}/></button></div>}
    {selected&&<><div className="detail-scrim" onClick={closePlace}/><aside className="detail-panel" role="dialog" aria-modal="true" aria-labelledby="place-title" ref={panelRef}><div className="detail-top"><button ref={closeRef} className="back-button" onClick={closePlace}><ArrowLeft size={18}/>Natrag na kartu</button><button className="round-button" onClick={closePlace} aria-label="Zatvori informacije"><X size={19}/></button></div><div className="place-emblem" style={{'--emblem':categories.find(c=>c.id===selected.category)?.color} as React.CSSProperties}><Icon name={selected.icon} size={62}/><span>{categories.find(c=>c.id===selected.category)?.name}</span></div><div className="detail-content"><p className="eyebrow">UPOZNAJ ZOO ZAGREB</p><h2 id="place-title">{selected.name}</h2><p className="place-description">{selected.description}</p><div className="place-location"><MapPin size={19}/><div><strong>Na karti Zoo-a</strong><span>{selected.lat.toFixed(5)}° N · {selected.lon.toFixed(5)}° E</span></div></div><button className="focus-button" onClick={()=>{doAction('focus',selected.point);closePlace();}}><Crosshair size={18}/>Pogledaj na karti</button><div className="visitor-note"><Leaf size={20}/><p>Promatraj mirno, ostani na stazi i slijedi upute uz nastambu.</p></div><a className="source-link" href={selected.source} target="_blank" rel="noreferrer">Izvor podataka <ArrowUpRight size={15}/></a><p className="verification-note">Položaj nije terenski potvrđen. Aktualnost sadržaja provjeri na lokaciji.</p></div></aside></>}
    {about&&<div className="about-overlay" onClick={()=>setAbout(false)}><section className="about-card" role="dialog" aria-modal="true" aria-labelledby="about-title" onClick={e=>e.stopPropagation()}><button autoFocus className="round-button about-close" onClick={()=>setAbout(false)} aria-label="Zatvori"><X size={20}/></button><Leaf size={30}/><p className="eyebrow">DOBRO JE ZNATI</p><h2 id="about-title">Zoo na dlanu.</h2><p>Neovisna pregledna verzija 3D karte Zoološkog vrta Zagreb. Prikaz je umjetnička interpretacija; detalji građevina i vegetacija nisu geodetska snimka.</p><p>Lokacija se prikazuje samo uz tvoje dopuštenje. Ne šaljemo je na poslužitelj i ne pohranjujemo povijest kretanja. Preciznost ovisi o uređaju i GPS signalu.</p><p>Geografski podaci: <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap, ODbL</a>, preuzeto 14. rujna 2026. Nazivi tematskih prostora: <a href="https://zoo.hr/karta/" target="_blank" rel="noreferrer">službena karta Zoo-a</a>. Sadržaj i GPS treba provjeriti na terenu prije uporabe kao pouzdanog vodiča.</p>{install?<button className="focus-button" onClick={async()=>{await install.prompt();const result=await install.userChoice;if(result.outcome==='accepted')setInstall(null);}}><ArrowDownToLine size={18}/>Dodaj na početni zaslon</button>:<p className="install-tip">Za brzi pristup odaberi „Dodaj na početni zaslon” u izborniku preglednika, ako je ta mogućnost dostupna.</p>}</section></div>}
  </main>;
}



