export const ORIGIN = { lat: 45.82155, lon: 16.0211 };
const R = 6378137;
const radians = Math.PI / 180;
export function toLocal(lat: number, lon: number): [number, number] {
  return [R * (lon - ORIGIN.lon) * radians * Math.cos(ORIGIN.lat * radians), R * (lat - ORIGIN.lat) * radians];
}
export function toCoordinates(x: number, north: number) {
  return { lat: ORIGIN.lat + north / R / radians, lon: ORIGIN.lon + x / (R * radians * Math.cos(ORIGIN.lat * radians)) };
}
export function inPolygon(point: number[], polygon: number[][]) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i], b = polygon[j];
    if ((a[1] > point[1]) !== (b[1] > point[1]) && point[0] < (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside;
}
export function locationQuality(accuracy: number) {
  return accuracy <= 20 ? 'good' : accuracy <= 60 ? 'approximate' : 'poor';
}
