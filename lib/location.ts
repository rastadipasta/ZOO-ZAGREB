import {toLocal,inPolygon} from './geo.ts';
export function locationError(code:number){return code===1?'Lokacija nije dopuštena. Možeš je omogućiti u postavkama preglednika.':code===3?'Lokacija nije pronađena na vrijeme. Pokušaj ponovno na otvorenom.':'GPS signal trenutačno nije dostupan. Pokušaj ponovno.';}
export function mapPosition(position:{coords:{latitude:number;longitude:number;accuracy:number};timestamp:number},boundary:number[][]){
  const {latitude,longitude,accuracy}=position.coords;
  if(![latitude,longitude,accuracy,position.timestamp].every(Number.isFinite)||latitude < -90||latitude>90||longitude < -180||longitude>180||accuracy<0)throw new Error('Invalid geolocation');
  const point=toLocal(latitude,longitude);return{point,accuracy,timestamp:position.timestamp,inside:inPolygon(point,boundary)};
}
