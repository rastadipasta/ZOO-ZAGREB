"""Deterministic Zagreb Zoo diorama. Blender 5.2 --background --python this_file.
Coordinates: X east, Y north, Z up; glTF export converts to Y up automatically.
Geography is OSM; architectural detail and vegetation are interpretive artwork.
"""
import bpy, math, json, random, pathlib, sys
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'blender'))
import animals
G=json.loads((ROOT/'data/geography.json').read_text(encoding='utf8'))
random.seed(42)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
palette={'earth':'b7a88c','grass':'9aaf66','grass2':'b8c985','sand':'d7c395','path':'efa444','edge':'f3dcb2','stone':'aea999','water':'42bcc4','waterlight':'79d4cf','wall':'d6c5a0','cream':'efe3ca','roof':'756554','roofdark':'494e45','wood':'806348','darkwood':'594838','glass':'609b9c','metal':'8a9c8f','leaf0':'345d32','leaf1':'427237','leaf2':'548542','leaf3':'709b43','leaf4':'8eac4e','animalbrown':'9b7350','animalgold':'b89759','animaldark':'49473c','animalwhite':'e3dfc7','black':'2f332b','pink':'d29687','purple':'9552a0'}
mats={};buckets={}
def rgb(s):
    def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
    return tuple(linear(int(s[i:i+2],16)/255) for i in (0,2,4))
for name,h in palette.items():
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb(h),1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb(h),1);bs.inputs['Roughness'].default_value=.85 if name!='water' else .32
    mats[name]=m;buckets[name]=[[],[]]
def mesh(mat,verts,faces):
    v,f=buckets[mat];off=len(v);v.extend(verts);f.extend([tuple(off+i for i in face) for face in faces])
def box(mat,c,s,ang=0):
    x,y,z=c;a,b,h=[q/2 for q in s];ca,sa=math.cos(ang),math.sin(ang)
    vs=[(x+u*ca-v*sa,y+u*sa+v*ca,z+w) for u,v,w in [(-a,-b,-h),(a,-b,-h),(a,b,-h),(-a,b,-h),(-a,-b,h),(a,-b,h),(a,b,h),(-a,b,h)]]
    mesh(mat,vs,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)])
def tube(mat,a,b,r,sides=6,r2=None):
    a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
    if u.length<.01:u=d.cross(Vector((0,1,0)))
    u.normalize();v=d.cross(u);r2=r if r2 is None else r2
    vs=[tuple(p+rad*(u*math.cos(i*2*math.pi/sides)+v*math.sin(i*2*math.pi/sides))) for p,rad in [(a,r),(b,r2)] for i in range(sides)]
    fs=[tuple(reversed(range(sides))),tuple(range(sides,sides*2))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    mesh(mat,vs,fs)
# One smooth-enough low-poly template, copied directly into material buffers.
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
ico=bpy.context.object;iv=[tuple(v.co) for v in ico.data.vertices];iff=[tuple(p.vertices) for p in ico.data.polygons];bpy.data.objects.remove(ico,do_unlink=True)
def ell(mat,c,s):
    vs=[]
    for i,v in enumerate(iv):
        noise=1+.17*math.sin(i*17.3+c[0]*1.9+c[1]*2.7) if mat.startswith('leaf') else 1
        vs.append((c[0]+v[0]*s[0]*noise,c[1]+v[1]*s[1]*noise,c[2]+v[2]*s[2]*noise))
    mesh(mat,vs,iff)
def polygon(mat,ps,z):
    ps=ps[:-1] if ps[0]==ps[-1] else ps
    if len(ps)<3:return
    vs=[Vector((p[0],p[1],z)) for p in ps]
    for tri in tessellate_polygon([vs]):mesh(mat,[tuple(vs[v] if isinstance(v,int) else v) for v in tri],[(0,1,2)])
def prism(mat,ps,z,h):
    polygon(mat,ps,z+h)
    for a,b in zip(ps,ps[1:]+ps[:1]):mesh(mat,[(a[0],a[1],z),(b[0],b[1],z),(b[0],b[1],z+h),(a[0],a[1],z+h)],[(0,1,2,3)])
def inside(p,ps):
    x,y=p;ok=False
    for a,b in zip(ps,ps[1:]+ps[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:ok=not ok
    return ok
def distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];l=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/l)) if l else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
def hull(points):
    ps=sorted(set(tuple(p) for p in points))
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lo=[];hi=[]
    for p in ps:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(ps):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]
features=G['features'];boundary=G['boundary'];water=[f for f in features if f['kind']=='water'];islands=[f for f in features if f['kind']=='island'];paths=[f for f in features if f['kind']=='path'];buildings=[f for f in features if f['kind']=='building'];enclosures=[f for f in features if f['kind']=='enclosure']
foot=hull(boundary+[p for f in water for p in f['points']]);cx=sum(p[0] for p in foot)/len(foot);cy=sum(p[1] for p in foot)/len(foot)
foot=[(cx+(p[0]-cx)*1.07,cy+(p[1]-cy)*1.1) for p in foot]
prism('earth',foot,-5,5);polygon('grass',foot,.02)
for f in water:polygon('water',f['points'],.16)
for f in islands:prism('grass',f['points'],.17,.3)
for f in enclosures:polygon('sand' if int(f['id'])%3 else 'grass2',f['points'],.2)
# Paths: round-ended strips avoid breaks at OSM way joins.
def path(ps,width,z,mat):
    for a,b in zip(ps,ps[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if not length:continue
        ux,uy=-dy/length*width/2,dx/length*width/2
        mesh(mat,[(a[0]+ux,a[1]+uy,z),(a[0]-ux,a[1]-uy,z),(b[0]-ux,b[1]-uy,z),(b[0]+ux,b[1]+uy,z)],[(0,1,2,3)])
    for p in ps:
        vs=[(p[0]+width/2*math.cos(i*math.tau/12),p[1]+width/2*math.sin(i*math.tau/12),z) for i in range(12)]
        mesh(mat,vs,[tuple(range(12))])
for f in paths:
    width=4.2 if f['tags'].get('highway')!='service' else 5.6
    path(f['points'],width+1.1,.32,'edge');path(f['points'],width,.35,'path')
    if f['tags'].get('bridge')=='yes':
        for a,b in zip(f['points'],f['points'][1:]):
            length=math.dist(a,b);ang=math.atan2(b[1]-a[1],b[0]-a[0]);nx,ny=-math.sin(ang),math.cos(ang)
            for sign in [-1,1]:
                for z in [.9,1.7]:tube('wood',(a[0]+sign*nx*2.2,a[1]+sign*ny*2.2,z),(b[0]+sign*nx*2.2,b[1]+sign*ny*2.2,z),.14)
            for i in range(int(length/.65)+1):
                t=i/max(1,int(length/.65));box('wood',(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,.43),(.45,4.4,.14),ang)
def fence(ps,height=1.75):
    for a,b in zip(ps,ps[1:]):
        length=math.dist(a,b)
        for z in [.75,height-.15]:tube('wood',(a[0],a[1],z),(b[0],b[1],z),.11)
        for i in range(max(1,int(length/3))):
            t=i/max(1,int(length/3));tube('darkwood',(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,.3),(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,height),.17)
for f in enclosures:fence(f['points'])
fence(boundary,1.35)
# Architectural footprints stay geographic. Roofs/windows are interpretive.
for f in buildings:
    ps=f['points'];name=f['tags'].get('name','');height=5.5 if name else 3.8
    if 'Paviljon' in name:height=7
    if 'dvor' in name:height=9
    prism('wall',ps,.4,height)
    center=f['center'];edges=list(zip(ps,ps[1:]));a,b=max(edges,key=lambda e:math.dist(*e));ang=math.atan2(b[1]-a[1],b[0]-a[0]);co,si=math.cos(ang),math.sin(ang)
    if len(ps)>22:
        polygon('roofdark',ps,height+.6)
        for aa,bb in edges:tube('roof',(*aa,height+.7),(*bb,height+.7),.2)
        continue
    local=[((p[0]-center[0])*co+(p[1]-center[1])*si,-(p[0]-center[0])*si+(p[1]-center[1])*co) for p in ps]
    xmin,xmax=min(p[0] for p in local)-.5,max(p[0] for p in local)+.5;ymin,ymax=min(p[1] for p in local)-.5,max(p[1] for p in local)+.5
    def tf(x,y,z):return (center[0]+x*co-y*si,center[1]+x*si+y*co,z)
    roofz=height+.5;ridge=roofz+min(4,(ymax-ymin)*.32)
    mesh('roofdark' if 'Tropska' in name else 'roof',[tf(xmin,ymin,roofz),tf(xmax,ymin,roofz),tf(xmax,ymax,roofz),tf(xmin,ymax,roofz),tf(xmin,(ymin+ymax)/2,ridge),tf(xmax,(ymin+ymax)/2,ridge)],[(0,1,5,4),(4,5,2,3),(0,4,3),(1,2,5)])
    # Ridge and fine ribs catch sunlight.
    tube('darkwood',tf(xmin,(ymin+ymax)/2,ridge),tf(xmax,(ymin+ymax)/2,ridge),.15)
    for i in range(int((xmax-xmin)/1.6)+1):
        x=xmin+i*1.6
        tube('wood',tf(x,ymin,roofz+.06),tf(x,(ymin+ymax)/2,ridge+.06),.035,4)
        tube('wood',tf(x,ymax,roofz+.06),tf(x,(ymin+ymax)/2,ridge+.06),.035,4)
    for a,b in edges:
        length=math.dist(a,b);theta=math.atan2(b[1]-a[1],b[0]-a[0])
        for i in range(1,int(length/3)):
            t=i/(int(length/3));pos=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,2.7)
            box('darkwood',pos,(1.25,.24,1.9),theta);box('glass',(pos[0],pos[1],pos[2]+.05),(.96,.3,1.5),theta)
    if 'dvor' in name:
        x,y=center;tube('cream',(x,y,.4),(x,y,12),2.6,8);tube('roofdark',(x,y,12),(x,y,16),3.1,8,.02)
# Tree clusters: varied silhouettes, layered leaf masses, natural spacing.
segments=[(a,b) for f in paths for a,b in zip(f['points'],f['points'][1:])]
def iswater(p):return any(inside(p,f['points']) for f in water) and not any(inside(p,f['points']) for f in islands)
treepos=[]
minx,maxx=min(p[0] for p in foot),max(p[0] for p in foot);miny,maxy=min(p[1] for p in foot),max(p[1] for p in foot)
for _ in range(10500):
    p=(random.uniform(minx,maxx),random.uniform(miny,maxy))
    if not inside(p,foot) or iswater(p):continue
    if any(distance(p,*s)<4.3 for s in segments):continue
    if any(inside(p,f['points']) for f in buildings):continue
    inpen=any(inside(p,f['points']) for f in enclosures)
    if inpen and random.random()>.10:continue
    if any(math.dist(p,q)<5.1 for q in treepos):continue
    treepos.append(p)
    if len(treepos)>=720:break
for x,y in treepos:
    h=random.uniform(7,13);r=random.uniform(2.2,3.9)
    tube('wood',(x,y,.15),(x,y,h*.7),.35,6,.16)
    for j in range(14):
        angle=j*2.4;spread=r*random.uniform(.25,.9);z=h*.65+random.uniform(-1.4,2.1)
        ell('leaf'+str(random.choices(range(5),weights=[1,2,4,3,1])[0]),(x+math.cos(angle)*spread,y+math.sin(angle)*spread,z),(r*.72,r*.7,r*random.uniform(.65,1)))
# Rock groups and grass tufts enrich enclosure surfaces.
for f in enclosures:
    ps=f['points'];cx,cy=f['center']
    for j in range(4):
        p=random.choice(ps);x=p[0]*.8+cx*.2;y=p[1]*.8+cy*.2
        ell('stone',(x,y,.65),(random.uniform(.6,1.4),random.uniform(.6,1.3),random.uniform(.5,1.2)))
    for j in range(12):
        p=random.choice(ps);x=p[0]*.65+cx*.35+random.uniform(-2,2);y=p[1]*.65+cy*.35+random.uniform(-2,2)
        for k in range(3):tube('leaf3',(x+k*.18,y,.3),(x+k*.18+.14,y+.12,random.uniform(.6,1.2)),.05,3,.005)
# Chibi animal assets are generated later as linked, reusable mesh instances.
# Aviary ribbed domes and glass pavilions.
for f in enclosures:
    if not any(q in f['tags'].get('name','').lower() for q in ['volijera','sup']):continue
    x,y=f['center'];r=8
    for a in range(12):
        theta=a*math.tau/12;prev=None
        for j in range(9):
            phi=j/8*math.pi/2;p=(x+r*math.cos(phi)*math.cos(theta),y+r*math.cos(phi)*math.sin(theta),.3+r*math.sin(phi))
            if prev:tube('metal',prev,p,.08,4)
            prev=p
    for z in [1.5,3,4.5,6]:
        rr=math.sqrt(r*r-z*z);ps=[(x+rr*math.cos(j*math.tau/32),y+rr*math.sin(j*math.tau/32),z+.3) for j in range(33)]
        for a,b in zip(ps,ps[1:]):tube('metal',a,b,.045,4)
# Benches beside pathways, plus warm plaza accents.
for f in paths[::4]:
    if not f['points']:continue
    x,y=f['points'][0];box('wood',(x+3.5,y,.9),(2.5,.8,.2));box('wood',(x+3.5,y+.45,1.35),(2.5,.15,.7))
    for xx in [-.8,.8]:box('darkwood',(x+3.5+xx,y,.5),(.15,.7,.8))
print('Building material batches...',flush=True)
for name,(verts,faces) in buckets.items():
    if not verts:continue
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(mats[name]);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    if name.startswith('leaf') or name.startswith('animal') or name in ['water','waterlight']:
        for p in me.polygons:p.use_smooth=True
scene=bpy.context.scene
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.75,.8,.9,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN',location=(-200,-200,300));sun=bpy.context.object;sun.rotation_euler=(.45,-.5,-.4);sun.data.energy=2.3;sun.data.angle=.15
bpy.ops.object.light_add(type='AREA',location=(0,0,250));bpy.context.object.data.energy=15000;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=400
bpy.ops.object.camera_add(location=(70,-510,500));cam=bpy.context.object;target=Vector((60,40,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=660;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
scene.view_settings.view_transform='AgX'
(ROOT/'public/models').mkdir(parents=True,exist_ok=True)
print('Building 21 reusable chibi animal assets...',flush=True)
animal_assets,animal_library=animals.build_library(ROOT)
animal_instances=animals.place_existing(enclosures,animal_assets)
animals.render_contact_sheet(ROOT,animal_assets)
bpy.context.window.scene=scene
animals.select_main_export_objects(scene,animal_library)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/zoo-zagreb.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
scene.render.filepath=str(ROOT/'blender/preview.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/zoo-zagreb.blend'))
print('DONE: Blender source, 22 GLBs and two previews saved.',flush=True)
