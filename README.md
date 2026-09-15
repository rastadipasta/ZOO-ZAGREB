# Zoo Zagreb · Interaktivna 3D karta

React + TypeScript + React Three Fiber web/PWA. Blender 5.2 generira model preko Python skripte. Aplikacija koristi stvarne OpenStreetMap tlocrte i stilizirani izgled inspiriran priloženom referencom.

## Pokretanje

```powershell
npm ci
npm run dev
npm test
npm run build
```

Na ovom Windows računalu radi i izravan poziv `node scripts/build.mjs`. Produkcijski rezultat je `dist/client`. Aplikacija se objavljuje kao statična HTTPS stranica; nema baze ni poslužiteljskog praćenja lokacije. Vite statična izgradnja izbjegava problem zatvaranja procesa Vinext/Node na Windowsu. Izvorne starter ovisnosti zadržane su u zaključanoj datoteci.

## Vercel

Repozitorij je pripremljen za Vercel kroz `vercel.json`. Nakon uvoza GitHub repozitorija `rastadipasta/ZOO-ZAGREB` postavke su:

- Framework preset: Vite
- Install command: `npm ci`
- Build command: `npm run build`
- Output directory: `dist/client`
- Environment variables: nisu potrebne

Vercel će nakon svakog push-a na `main` izraditi produkcijsku objavu, a za pull request grane preglednu objavu.

## Blender

```powershell
npm run blender:build
```

Naredba kroz Blender 5.2 generira i provjerava `blender/zoo-zagreb.blend`, pregled cijele karte `blender/preview.png`, kontaktni pregled `blender/animals-preview.png`, glavni `public/models/zoo-zagreb.glb` i 21 zasebni chibi asset u `public/models/animals/`. Na karti se koristi 29 povezanih instanci na 21 postojećoj lokaciji. Svaka životinja je jedan multi-material mesh, ima ishodište u sredini i stopala na Z=0.

GLB datoteke su komprimirane Dracom, a dekoder se poslužuje lokalno. Vegetacija, arhitektonski detalji i minijature životinja umjetnička su interpretacija, a ne geodetski model. Nema vanjskog API ključa niti poziva AI modela iz aplikacije.

## Sadržaj i geografska veza

- `data/osm-zoo.xml`: OSM snimka preuzeta 14. rujna 2026. preko službenog API-ja, bbox 16.0170,45.8190,16.0260,45.8240.
- `data/geography.json`: reproducibilna geometrija u metrima; kopija za preuzimanje je `public/data/geography.json`.
- `lib/places.ts`: nazivi, kategorije, opisi i izvori informativnih točaka. Tematske točke bez izravnog OSM objekta približno su postavljene prema službenoj karti.
- `lib/geo.ts`: zajedničko ishodište 45.82155 N, 16.0211 E i dvosmjerna pretvorba WGS84/lokalne metre. Blender X je istok, Y sjever, Z visina; glTF ih pretvara u X istok, Y visina, Z jug.
- OSM podaci: © OpenStreetMap contributors, ODbL 1.0: https://www.openstreetmap.org/copyright
- Službena karta: https://zoo.hr/karta/ (slika objavljena u prosincu 2025.). Dostavljena slika koristi se kao vizualna referenca, nije prikazana kao zamjena za 3D.

## Provjere i granice izdanja

10 automatiziranih testova pokriva pretvorbu koordinata, rubne vrijednosti GPS preciznosti, položaj izvan Zoo-a, neispravne podatke, odbijanje dopuštenja, nedostupan signal i timeout. Preglednik je korišten za provjeru desktop i 390 × 844 mobilnog prikaza, kategorija te otvaranja i zatvaranja informativnog panela. WebMCP otvaranje poznate točke i odbijanje nepoznatog ID-a provjereni su tijekom izrade.

Terenski GPS, aktualni stanovnici svih nastambi, pristupačnost objekata i cilj od 30 FPS na fizičkom mobitelu srednje klase nisu potvrđeni. Prije uporabe kao vodiča za posjetitelje treba izmjeriti položaje na ulazima, mostovima i raskrižjima; evidentirati odstupanja i aktualizirati podatke. Do tada izdanje ostaje jasno označena neovisna pregledna verzija.

Lokacija se traži samo pritiskom gumba. Ne šalje se na poslužitelj i ne zapisuje se povijest. Prikazuju se krug preciznosti, nedostupan signal, zastarjela lokacija i položaj izvan vrta. Praćenje se može isključiti. Predmemorija PWA čuva posjećene sadržaje; prvo otvaranje zahtijeva internet. Nema izračuna ruta.

Za novu objavu s izmjenom datoteka koje nemaju hash u nazivu povećaj verziju `CACHE` u `public/sw.js`.
