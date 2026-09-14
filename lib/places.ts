import geography from '../data/geography.json';
import { toCoordinates } from './geo';
export type Category = 'animals' | 'services' | 'care' | 'entrance' | 'heritage';
export type Place = { id: string; name: string; point: number[]; category: Category; icon: string; description: string; source: string; verified: boolean; lat: number; lon: number; featured?: boolean };
const official = 'https://zoo.hr/karta/';
const content: Partial<Record<string, { name?: string; icon: string; description: string; featured?: boolean }>> = {
  '311979811': { name: 'Lavlja stijena Kidepo', icon: 'cat', description: 'Nastamba afričkih lavova. Promatraj prostor među stijenama i zaklonima — životinje mogu odmarati izvan pogleda posjetitelja.', featured: true },
  '311979814': { name: 'Europski bizon', icon: 'beef', description: 'Nastamba europskih bizona. Istraži ograđeni vanjski prostor, a više o vrsti pročitaj na edukativnoj ploči uz nastambu.' },
  '311979819': { name: 'Zebre', icon: 'horse', description: 'Nastamba Grantovih stepskih zebri. Zadrži se uz ogradu i promotri prepoznatljive pruge te kretanje životinja po otvorenom prostoru.', featured: true },
  '311980666': { icon: 'beef', description: 'Nastamba dvogrbih deva. S posjetiteljske staze možeš promatrati vanjski prostor i pročitati zanimljivosti na obližnjoj ploči.' },
  '311981705': { icon: 'turtle', description: 'Tropska kuća okuplja nastambe različitih životinja. Slijedi oznake na ulazu i zaviri u unutarnje prostore kada su otvoreni za posjetitelje.', featured: true },
  '311993719': { name: 'Dječji Zoo', icon: 'beef', description: 'Prostor namijenjen upoznavanju domaćih životinja. Za ulazak i kontakt sa životinjama slijedi istaknute upute djelatnika.', featured: true },
  '311993237': { name: 'Paviljon za majmune', icon: 'paw', description: 'Paviljon za majmune jedan je od prepoznatljivih objekata Zoo-a. Istraži nastambe uz paviljon i edukativne sadržaje.', featured: true },
  '311993457': { name: 'Staza savjesti', icon: 'footprints', description: 'Tematska točka koja poziva na razmišljanje o odnosu ljudi prema prirodi. Zastani i pročitaj poruke uz stazu.' },
  '380607172': { icon: 'bird', description: 'Prohodna volijera za afričke ptice. Prije ulaska pročitaj upute i pažljivo zatvori vrata za sobom.', featured: true },
  '724699308': { icon: 'paw', description: 'Tematska nastamba Madagaskar nalazi se u zapadnom dijelu vrta. Upoznaj životinje i priče povezane s ovim otokom.', featured: true },
  '710721722': { name: 'Bjeloglavi supovi i ćelavi ibisi', icon: 'bird', description: 'Volijera označena na službenoj karti kao nastamba u koju se može ući. Prati pravila istaknuta na ulazu.' },
  '770653677': { name: 'Australija', icon: 'paw', description: 'Australska tematska nastamba, uz staze zapadnog dijela Zoo-a. Aktualne stanovnike provjeri na pločama uz nastambu.', featured: true },
  '770678484': { icon: 'cat', description: 'Nastamba crvenog pande. Pogledaj i prema granama i povišenim odmorištima; životinja može biti skrivena u zelenilu.' },
  '772922521': { name: 'Kišna Afrika', icon: 'beef', description: 'Tematski prostor Kišna Afrika nalazi se uz istočni dio vrta. Nastamba patuljastog vodenkonja označena je u geografskim podacima na ovoj lokaciji.' },
  '311992534': { icon: 'waves', description: 'Bazen i nastamba kalifornijskih morskih lavova, uz restoran i istočni dio posjetiteljske staze.' },
  '3839233946': { name: 'Ulaz 1', icon: 'door', description: 'Ulaz preko mosta uz Prvo Maksimirsko jezero. Aktualno radno vrijeme i ulaznice provjeri na službenim stranicama Zoo-a.', featured: true },
};
function infer(name: string, category: Category) {
  if (category === 'entrance') return 'door';
  if (name === 'WC') return 'wc';
  if (name.includes('Suvenir')) return 'gift';
  if (/ptice|sup|sova|Jastreba|Pelikan|Noj|kljunoro/i.test(name)) return 'bird';
  if (/kornja/i.test(name)) return 'turtle';
  if (/deva|Bizon|Alpaka|Ljama|oriks|tapir|konj/i.test(name)) return 'beef';
  if (/lav|panda|leopard|Ris|Serval/i.test(name)) return 'cat';
  return 'paw';
}
const excluded = new Set(['311979817']); // Old wolf location conflicts with construction on the official map.
const base: Place[] = geography.pois.filter(p => !excluded.has(p.id.replace('osm-', ''))).map(p => {
  const extra = content[p.id.replace('osm-', '')];
  const category = p.category as Category;
  return { ...p, category, icon: infer(p.name, category), description: category === 'animals' ? 'Ova je nastamba označena u geografskim podacima Zoo-a. Aktualne stanovnike i informacije provjeri na edukativnoj ploči uz nastambu.' : p.name === 'WC' ? 'Sanitarni prostor uz posjetiteljsku stazu. Prati oznake na objektu.' : 'Mjesto za uspomenu na posjet Zoo-u. Dostupnost i radno vrijeme provjeri na lokaciji.', ...extra, ...toCoordinates(p.point[0], p.point[1]) };
});
const additional: Array<[string, string, number[], Category, string, string]> = [
  ['restaurant','Kod morskog lava',[253.37,117.44],'services','utensils','Restoran uz nastambu morskih lavova. Ponudu i radno vrijeme provjeri na službenim stranicama ili u restoranu.'],
  ['education','Edukacijski centar',[249.3,180.89],'services','house','Edukacijski prostor Zoo-a. Za programe i organizirane posjete provjeri službene informacije.'],
  ['old-house','Domaća hiža',[233.5,201.4],'animals','mouse','Tematski prostor Domaća hiža, označen u sjeveroistočnom dijelu službene karte.'],
  ['micro','Mikrosvijet Maksimirske šume',[253,162],'animals','bug','Istraži edukativni sadržaj posvećen malim stanovnicima Maksimirske šume.'],
  ['swan','Labuđi otok',[-36,44],'animals','bird','Otok na Prvom Maksimirskom jezeru, povezan s posjetiteljskim stazama. Položaj je približno prenesen sa službene ilustrirane karte.'],
  ['pollinators','Vrt oprašivača',[-21,31],'animals','flower','Vrt posvećen oprašivačima i njihovoj ulozi u prirodi. Položaj je približno prenesen sa službene karte.'],
  ['sichuan','Sichuan',[29.74,38.37],'animals','house','Tematski prostor s kineskim paviljonom, uz jezero i središnje staze.'],
  ['african-village','Afričko selo',[163,25],'animals','house','Tematski prostor Afričko selo, u blizini Tropske kuće.'],
  ['trapper','Traperska koliba',[163.49,-16.47],'animals','house','Prepoznatljiv objekt uz južni dio vrta, označen na službenoj karti.'],
  ['twilight','Zona sumraka',[175,32],'animals','moon','Tematski sadržaj uz Tropsku kuću. Prati oznake na objektu za pristup unutarnjem prostoru.'],
  ['monsoon','Duh monsunskih šuma',[177,14],'animals','bird','Tematski sadržaj u istočnom dijelu Zoo-a, označen na službenoj karti.'],
  ['zebrasquare','Zebrin trg',[88,37],'heritage','landmark','Središnji trg na spoju nekoliko posjetiteljskih staza. Dobra točka za kratku stanku i orijentaciju.'],
  ['tower','Začarani dvor',[-134.88,-2.23],'heritage','landmark','Povijesni objekt u blizini Ulaza 1, uz jezero.'],
  ['bridge','Lavlji most',[9,-10],'heritage','landmark','Most označen na službenoj karti kao dio kulturne i povijesne baštine Zoo-a. Skulpture potpisuje Josip Turkalj.'],
  ['aid-west','Prva pomoć · Ulaz 1',[-113,5],'care','plus','Točka prve pomoći prema službenoj karti. Za pomoć se obrati djelatniku Zoo-a; u hitnom slučaju nazovi 112.'],
  ['aed-east','AED · Restoran',[255,110],'care','heart','Lokacija AED-a prema službenoj karti, uz zonu restorana. Položaj uređaja potvrdi kod djelatnika.'],
  ['entry-2','Ulaz 2',[199,-4],'entrance','door','Ulaz 2 s istočne strane vrta, označen na službenoj karti. Dostupnost ovog ulaza provjeri prije dolaska.'],
];
export const places: Place[] = [...base, ...additional.map(([id,name,point,category,icon,description]) => ({id,name,point,category,icon,description,source:official,verified:false,...toCoordinates(point[0],point[1])}))];
export const categories: Array<{ id: Category | 'all'; name: string; color: string; icon: string }> = [
  {id:'all',name:'Sve na karti',color:'#325b36',icon:'map'},
  {id:'animals',name:'Nastambe i centri',color:'#78398a',icon:'paw'},
  {id:'services',name:'Usluge',color:'#d97920',icon:'utensils'},
  {id:'care',name:'Pomoć i sigurnost',color:'#238650',icon:'heart'},
  {id:'heritage',name:'Baština i trgovi',color:'#807253',icon:'landmark'},
  {id:'entrance',name:'Ulazi',color:'#d6423e',icon:'door'},
];
export { geography };
