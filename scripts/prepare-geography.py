"""Convert the attributed OSM snapshot to a reproducible local metre grid."""
import json, math, pathlib, xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]
tree = ET.parse(ROOT/'data/osm-zoo.xml').getroot()
LAT, LON = 45.82155, 16.0211
R = 6378137
def xy(lat,lon):
    return [round(R*math.radians(float(lon)-LON)*math.cos(math.radians(LAT)),3),round(R*math.radians(float(lat)-LAT),3)]
nodes={n.attrib['id']:n for n in tree.findall('node')}
def tags(e): return {t.attrib['k']:t.attrib['v'] for t in e.findall('tag')}
def points(w): return [xy(nodes[n.attrib['ref']].attrib['lat'],nodes[n.attrib['ref']].attrib['lon']) for n in w.findall('nd') if n.attrib['ref'] in nodes]
ways=[{'id':w.attrib['id'],'tags':tags(w),'points':points(w)} for w in tree.findall('way')]
boundary=next(w['points'] for w in ways if w['tags'].get('tourism')=='zoo')
def inside(p, poly=boundary):
    x,y=p; result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result
def center(ps):return [sum(p[i] for p in ps)/len(ps) for i in (0,1)]
features=[]
for w in ways:
    p,t=w['points'],w['tags']
    if len(p)<2:continue
    c=center(p)
    near=any(inside(q) for q in p) or inside(c)
    if t.get('tourism')=='zoo':continue
    kind=None
    if t.get('natural')=='water' or t.get('water'): kind='water'
    elif t.get('highway') in ['footway','path','pedestrian','steps','service'] and near:kind='path'
    elif t.get('highway') in ['primary','secondary','tertiary','residential'] and -230<c[0]<270 and -200<c[1]<280:kind='road'
    elif t.get('building') and near:kind='building'
    elif t.get('attraction')=='animal' and near:kind='enclosure'
    elif t.get('barrier') in ['fence','wall'] and near:kind='fence'
    if kind and w['id']!='29582725':features.append({**w,'kind':kind,'center':center(p)})
for rel in tree.findall('relation'):
    if tags(rel).get('natural')!='water':continue
    for member in rel.findall('member'):
        w=next((w for w in ways if w['id']==member.attrib['ref']),None)
        if w and w['points']:
            features.append({**w,'kind':'water' if member.attrib['role']=='outer' else 'island','center':center(w['points'])})
pois=[]
for w in features:
    t=w['tags']
    if t.get('attraction')=='animal' and t.get('name'):
        pois.append({'id':'osm-'+w['id'],'name':t['name'].replace(';', ' · '),'point':w['center'],'category':'animals','animal':t.get('animal',''),'source':'https://www.openstreetmap.org/way/'+w['id'],'verified':False})
for n in nodes.values():
    t=tags(n);p=xy(n.attrib['lat'],n.attrib['lon'])
    if not inside(p):continue
    category=None
    if t.get('amenity')=='toilets':category='services';name='WC'
    elif t.get('amenity')=='restaurant':category='services';name=t.get('name','Restoran')
    elif t.get('shop')=='gift':category='services';name='Suvenirnica'
    elif t.get('entrance') in ['yes','main'] and t.get('barrier')=='gate':category='entrance';name='Ulaz'
    elif t.get('emergency')=='defibrillator':category='care';name='AED defibrilator'
    if category:pois.append({'id':'osm-'+n.attrib['id'],'name':name,'point':p,'category':category,'animal':'','source':'https://www.openstreetmap.org/node/'+n.attrib['id'],'verified':False})
result={'origin':{'lat':LAT,'lon':LON},'boundary':boundary,'features':features,'pois':pois,'attribution':'© OpenStreetMap contributors · ODbL 1.0','source':'https://www.openstreetmap.org/copyright','retrieved':'2026-09-14','fieldVerified':False}
(ROOT/'data/geography.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf8')
print(json.dumps({'features':len(features),'pois':len(pois)}))
