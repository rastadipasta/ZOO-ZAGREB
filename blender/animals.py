"""Procedural, reusable chibi animal assets for the Zagreb Zoo map.

Every asset is built at the origin, faces -Y, has its feet on Z=0 and is joined
to one multi-material mesh.  The same mesh datablock is linked into the map and
exported as a standalone GLB.
"""
import math
from pathlib import Path

import bpy
from mathutils import Vector


ASSETS = (
    "african-lion", "european-bison", "plains-zebra", "bactrian-camel",
    "eurasian-lynx", "goat", "serval", "chinese-leopard", "ostrich",
    "african-bird", "lowland-tapir", "scimitar-oryx", "griffon-vulture",
    "snowy-owl", "jastrebaca-owl", "pelican", "mongolian-wild-horse",
    "llama", "red-panda", "pygmy-hippo", "brown-bear",
)

# Existing enclosure IDs only. The second placement preserves the old generator's
# offset and scale, so this remains exactly 29 figures across 21 locations.
PLACEMENTS = {
    "311979811": ("african-lion", 1),
    "311979814": ("european-bison", 1),
    "311979819": ("plains-zebra", 2),
    "311980666": ("bactrian-camel", 2),
    "311992928": ("eurasian-lynx", 1),
    "311993719": ("goat", 1),
    "311996825": ("serval", 1),
    "312000927": ("chinese-leopard", 1),
    "312001668": ("ostrich", 2),
    "380607172": ("african-bird", 2),
    "509558887": ("lowland-tapir", 1),
    "601762731": ("scimitar-oryx", 2),
    "710721722": ("griffon-vulture", 2),
    "724697080": ("snowy-owl", 1),
    "724698227": ("jastrebaca-owl", 1),
    "770631120": ("pelican", 1),
    "770667730": ("mongolian-wild-horse", 2),
    "770667732": ("llama", 2),
    "770678484": ("red-panda", 1),
    "772922521": ("pygmy-hippo", 1),
    "923053787": ("brown-bear", 1),
}

COLORS = {
    "black": "24262a", "white": "f7f3ea", "cream": "f2d7a2",
    "tan": "c88b52", "brown": "815036", "dark-brown": "49312b",
    "gold": "f2a51a", "orange": "eb7114", "rust": "b9472d",
    "red": "c94e35", "pink": "f28ca7", "rose": "e56479",
    "grey": "7a7d87", "light-grey": "c9cbd0", "dark-grey": "43464e",
    "blue": "5ba8d1", "green": "6e9c58", "yellow": "f4c842",
}

BASE = {
    "african-lion": ("gold", "cream"), "european-bison": ("brown", "tan"),
    "plains-zebra": ("white", "light-grey"), "bactrian-camel": ("tan", "cream"),
    "eurasian-lynx": ("tan", "cream"), "goat": ("white", "cream"),
    "serval": ("gold", "cream"), "chinese-leopard": ("orange", "cream"),
    "ostrich": ("dark-grey", "white"), "african-bird": ("blue", "cream"),
    "lowland-tapir": ("dark-grey", "light-grey"), "scimitar-oryx": ("white", "cream"),
    "griffon-vulture": ("brown", "cream"), "snowy-owl": ("white", "light-grey"),
    "jastrebaca-owl": ("brown", "tan"), "pelican": ("white", "cream"),
    "mongolian-wild-horse": ("tan", "cream"), "llama": ("cream", "white"),
    "red-panda": ("orange", "cream"), "pygmy-hippo": ("grey", "light-grey"),
    "brown-bear": ("brown", "cream"),
}


def _linear(hex_value):
    values = [int(hex_value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values)


def ensure_materials():
    materials = {}
    for name, value in COLORS.items():
        full_name = f"Chibi.{name}"
        material = bpy.data.materials.get(full_name) or bpy.data.materials.new(full_name)
        color = _linear(value)
        material.diffuse_color = (*color, 1)
        material.use_nodes = True
        shader = material.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (*color, 1)
        shader.inputs["Roughness"].default_value = .38
        materials[name] = material
    return materials


def _finish(obj, material):
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def _sphere(parts, material, location, scale, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.scale = scale
    parts.append(_finish(obj, material))
    return obj


def _cone(parts, material, location, scale, vertices=12, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=1, radius2=0, depth=2, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.scale = scale
    parts.append(_finish(obj, material))
    return obj


def _capsule(parts, material, start, end, radius, vertices=10, end_caps=True):
    a, b = Vector(start), Vector(end)
    direction = b - a
    midpoint = (a + b) * .5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=direction.length, location=midpoint)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    parts.append(_finish(obj, material))
    if end_caps:
        _sphere(parts, material, a, (radius, radius, radius), 12, 6)
        _sphere(parts, material, b, (radius, radius, radius), 12, 6)
    return obj


def _ear(parts, mats, side, z, outer, inner="pink", tall=False, tuft=False):
    sx = .25 if tall else .34
    sz = .58 if tall else .38
    _cone(parts, mats[outer], (side, -.02, z), (sx, .18, sz), 3)
    _cone(parts, mats[inner], (side, -.19, z - .02), (sx * .48, .035, sz * .55), 3)
    if tuft:
        _cone(parts, mats["black"], (side, -.01, z + sz * .82), (.09, .08, .22), 5)


def _eyes(parts, mats, z=3.55, spread=.35, size=.115, iris=None):
    for x in (-spread, spread):
        if iris:
            _sphere(parts, mats[iris], (x, -.755, z), (size * 1.42, .075, size * 1.42), 12, 6)
        _sphere(parts, mats["black"], (x, -.805, z), (size, .07, size * 1.1), 12, 6)
        _sphere(parts, mats["white"], (x - .035, -.87, z + .045), (.026, .018, .026), 8, 4)


def _muzzle(parts, mats, patch, z=3.22, scale=(.48, .25, .28), nose="dark-brown"):
    _sphere(parts, mats[patch], (0, -.76, z), scale)
    _sphere(parts, mats[nose], (0, -.99, z + .05), (.15, .11, .105), 12, 6)


def _limbs(parts, mats, body, hoof=None):
    for x in (-.52, .52):
        _capsule(parts, mats[body], (x, -.02, 2.05), (x * 1.42, -.08, 1.35), .16)
    for x in (-.28, .28):
        _capsule(parts, mats[body], (x, 0, 1.18), (x, -.02, .30), .19)
        _sphere(parts, mats[hoof or body], (x, -.09, .20), (.24, .31, .18), 12, 6)


def _spots(parts, mats, count, color="dark-brown", head=False):
    coords = [(-.36, 1.86), (.31, 2.03), (-.08, 1.55), (.42, 1.44), (-.45, 2.28),
              (-.46, 3.68), (.15, 3.82), (.43, 3.38), (-.12, 3.22), (.28, 3.05)]
    for x, z in coords[:count]:
        if not head and z > 3:
            continue
        _sphere(parts, mats[color], (x, -.535 if z < 3 else -.775, z), (.09, .035, .09), 10, 5)


def build_asset(asset_id, mats):
    body, patch = BASE[asset_id]
    parts = []
    bird = asset_id in {"ostrich", "african-bird", "griffon-vulture", "snowy-owl", "jastrebaca-owl", "pelican"}
    long_neck = asset_id in {"ostrich", "llama"}

    # Shared toy-like silhouette.
    _sphere(parts, mats[body], (0, 0, 1.72), (.66, .52, .92))
    _sphere(parts, mats[patch], (0, -.48, 1.70), (.42, .12, .60))
    _limbs(parts, mats, body, "dark-brown" if asset_id in {"bison", "goat"} else None)
    if long_neck:
        _capsule(parts, mats[body], (0, 0, 2.15), (0, 0, 3.25), .30)
        head_z = 3.85
    else:
        head_z = 3.35
    head_scale = (1.0, .82, .88) if asset_id in {"pygmy-hippo", "brown-bear"} else (.88, .76, .86)
    _sphere(parts, mats[body], (0, 0, head_z), head_scale)

    # Mammal ears, with species-specific silhouettes.
    if not bird:
        tall = asset_id in {"serval", "plains-zebra", "mongolian-wild-horse", "llama", "scimitar-oryx", "goat"}
        tuft = asset_id == "eurasian-lynx"
        for side in (-.58, .58):
            _ear(parts, mats, side, head_z + .72, body, tall=tall, tuft=tuft)

    eye_z = head_z + .12
    if asset_id in {"snowy-owl", "jastrebaca-owl"}:
        for x in (-.34, .34):
            _sphere(parts, mats[patch], (x, -.69, eye_z), (.34, .08, .38))
        _eyes(parts, mats, eye_z, .34, .13, "yellow")
    else:
        _eyes(parts, mats, eye_z, .34 if not bird else .28, .11)

    # Faces and defining details.
    if asset_id == "african-lion":
        for i in range(14):
            a = math.tau * i / 14
            _sphere(parts, mats["rust"], (.78 * math.cos(a), .13, head_z + .74 * math.sin(a)), (.36, .28, .38), 12, 6)
        _muzzle(parts, mats, patch, head_z - .20)
    elif asset_id == "european-bison":
        _sphere(parts, mats["dark-brown"], (0, .08, head_z + .22), (1.02, .77, .72))
        _sphere(parts, mats[body], (0, -.12, head_z), (.86, .70, .66))
        _eyes(parts, mats, eye_z, .34, .11)
        _muzzle(parts, mats, patch, head_z - .25, (.54, .28, .32), "black")
        for s in (-1, 1):
            _cone(parts, mats["cream"], (s * .77, -.03, head_z + .43), (.13, .13, .42), 10, (0, s * .72, 0))
    elif asset_id == "plains-zebra":
        _muzzle(parts, mats, "light-grey", head_z - .25, (.48, .28, .31), "black")
        for x, z, rot in [(-.42, 3.75, -.35), (.34, 3.55, .25), (-.28, 2.12, -.2), (.29, 1.82, .25), (-.18, 1.45, -.2)]:
            _capsule(parts, mats["black"], (x - .25, -.53, z), (x + .25, -.53, z + rot), .055, 8, False)
        for i in range(5):
            _sphere(parts, mats["black"], (0, .55, 3.6 - i * .3), (.12, .12, .20), 10, 5)
    elif asset_id == "bactrian-camel":
        _sphere(parts, mats[body], (-.28, .26, 2.35), (.40, .38, .48))
        _sphere(parts, mats[body], (.28, .26, 2.35), (.40, .38, .48))
        _muzzle(parts, mats, patch, head_z - .28, (.54, .31, .30))
    elif asset_id == "eurasian-lynx":
        _muzzle(parts, mats, patch, head_z - .20)
        _spots(parts, mats, 9)
        for s in (-1, 1):
            _cone(parts, mats[patch], (s * .62, -.66, head_z - .18), (.18, .08, .28), 5, (0, 0, s * .65))
    elif asset_id == "goat":
        _muzzle(parts, mats, patch, head_z - .24)
        for s in (-1, 1):
            _cone(parts, mats["tan"], (s * .38, .05, head_z + .86), (.11, .11, .55), 10, (0, s * .28, 0))
        _cone(parts, mats["cream"], (0, -.71, head_z - .58), (.17, .09, .34), 6, (math.pi, 0, 0))
    elif asset_id in {"serval", "chinese-leopard"}:
        _muzzle(parts, mats, patch, head_z - .20)
        _spots(parts, mats, 10, "black")
        if asset_id == "serval":
            for s in (-1, 1):
                _sphere(parts, mats["black"], (s * .58, -.10, head_z + .72), (.18, .12, .32), 10, 5)
        else:
            _capsule(parts, mats[body], (.47, .34, 1.55), (1.05, .24, 1.05), .13)
    elif asset_id == "lowland-tapir":
        _sphere(parts, mats[patch], (0, -.77, head_z - .23), (.48, .33, .32))
        _capsule(parts, mats[patch], (0, -.90, head_z - .18), (0, -1.20, head_z - .42), .19)
        _sphere(parts, mats["black"], (0, -1.39, head_z - .44), (.19, .12, .13))
    elif asset_id == "scimitar-oryx":
        _muzzle(parts, mats, patch, head_z - .22)
        for s in (-1, 1):
            _capsule(parts, mats["dark-brown"], (s * .31, .02, head_z + .69), (s * .43, .04, head_z + 1.55), .07, 8)
        _capsule(parts, mats["dark-brown"], (0, -.75, head_z + .45), (0, -.78, head_z - .10), .075, 8, False)
    elif asset_id == "mongolian-wild-horse":
        _muzzle(parts, mats, patch, head_z - .24, (.49, .28, .31))
        for i in range(6):
            _sphere(parts, mats["dark-brown"], (0, .55, head_z + .62 - i * .28), (.14, .13, .22), 10, 5)
    elif asset_id == "llama":
        _muzzle(parts, mats, patch, head_z - .21)
        for x in (-.45, -.15, .15, .45):
            _sphere(parts, mats["white"], (x, -.03, head_z + .72), (.27, .26, .30), 12, 6)
    elif asset_id == "red-panda":
        for s in (-1, 1):
            _sphere(parts, mats["white"], (s * .34, -.70, eye_z), (.30, .08, .34))
        _eyes(parts, mats, eye_z, .34, .11)
        _muzzle(parts, mats, patch, head_z - .23, (.45, .24, .27), "black")
        _capsule(parts, mats["orange"], (.45, .35, 1.55), (1.15, .24, 1.25), .20)
        for i in range(3):
            _sphere(parts, mats["cream"], (.73 + i * .18, .15, 1.39 - i * .08), (.08, .16, .13), 10, 5)
    elif asset_id == "pygmy-hippo":
        _sphere(parts, mats[patch], (0, -.79, head_z - .24), (.67, .36, .39))
        for x in (-.24, .24):
            _sphere(parts, mats["dark-grey"], (x, -1.12, head_z - .16), (.075, .06, .075), 10, 5)
    elif asset_id == "brown-bear":
        for s in (-1, 1):
            _sphere(parts, mats[body], (s * .68, -.03, head_z + .65), (.35, .25, .35), 12, 6)
            _sphere(parts, mats[patch], (s * .68, -.25, head_z + .65), (.18, .05, .18), 10, 5)
        _muzzle(parts, mats, patch, head_z - .21, (.51, .27, .31), "black")
    elif asset_id == "ostrich":
        _sphere(parts, mats["pink"], (0, -.05, head_z), (.60, .58, .62))
        _eyes(parts, mats, eye_z, .25, .105)
        _cone(parts, mats["rose"], (0, -.78, head_z - .10), (.20, .42, .13), 4, (math.pi / 2, 0, 0))
        for s in (-1, 1):
            _sphere(parts, mats["white"], (s * .54, -.03, 1.88), (.30, .30, .58))
    elif asset_id == "african-bird":
        _cone(parts, mats["yellow"], (0, -.82, head_z - .10), (.22, .39, .14), 4, (math.pi / 2, 0, 0))
        for s in (-1, 1):
            _sphere(parts, mats["green"], (s * .57, -.02, 1.85), (.25, .22, .60))
        _sphere(parts, mats["red"], (0, .02, head_z + .72), (.18, .16, .25), 10, 5)
    elif asset_id in {"griffon-vulture", "pelican"}:
        if asset_id == "griffon-vulture":
            for i in range(9):
                a = math.tau * i / 9
                _sphere(parts, mats["cream"], (.53 * math.cos(a), .05, head_z - .18 + .37 * math.sin(a)), (.24, .19, .25), 10, 5)
            _sphere(parts, mats["pink"], (0, -.03, head_z), (.58, .55, .60))
            _cone(parts, mats["dark-brown"], (0, -.80, head_z - .12), (.18, .34, .13), 4, (math.pi / 2, 0, 0))
        else:
            _capsule(parts, mats["yellow"], (0, -.60, head_z - .10), (0, -1.35, head_z - .28), .22, 8)
            _sphere(parts, mats["orange"], (0, -1.18, head_z - .45), (.27, .25, .30), 12, 6)
    elif asset_id in {"snowy-owl", "jastrebaca-owl"}:
        beak = "dark-brown" if asset_id == "jastrebaca-owl" else "grey"
        _cone(parts, mats[beak], (0, -.84, head_z - .06), (.13, .26, .12), 4, (math.pi / 2, 0, 0))
        for s in (-1, 1):
            _sphere(parts, mats[patch], (s * .53, -.03, 1.82), (.25, .23, .61))
        if asset_id == "snowy-owl":
            _spots(parts, mats, 8, "grey")
        else:
            for s in (-1, 1):
                _cone(parts, mats["dark-brown"], (s * .48, -.02, head_z + .76), (.17, .13, .34), 4)

    # Join all primitives, consolidate identical material slots and normalize.
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = f"Asset.{asset_id}"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")

    source_slots = list(obj.data.materials)
    polygon_materials = [source_slots[polygon.material_index].name for polygon in obj.data.polygons]
    unique, material_lookup = [], {}
    for material in source_slots:
        key = material.name
        if key not in material_lookup:
            material_lookup[key] = len(unique)
            unique.append(material)
    obj.data.materials.clear()
    for material in unique:
        obj.data.materials.append(material)
    for polygon, material_name in zip(obj.data.polygons, polygon_materials):
        polygon.material_index = material_lookup[material_name]
    min_z = min(vertex.co.z for vertex in obj.data.vertices)
    for vertex in obj.data.vertices:
        vertex.co.z -= min_z
    obj.data.update()
    return obj


def _export_selected(path):
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_cameras=False, export_lights=False,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
    )


def build_library(root):
    mats = ensure_materials()
    library = bpy.data.collections.new("AnimalLibrary")
    bpy.context.scene.collection.children.link(library)
    assets = {}
    output = Path(root) / "public" / "models" / "animals"
    output.mkdir(parents=True, exist_ok=True)
    for asset_id in ASSETS:
        obj = build_asset(asset_id, mats)
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        library.objects.link(obj)
        assets[asset_id] = obj
        bpy.ops.object.select_all(action="DESELECT")
        obj.hide_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        _export_selected(output / f"{asset_id}.glb")
        obj.select_set(False)
        obj.hide_render = True
        obj.hide_set(True)
    library.hide_render = True
    return assets, library


def place_existing(features, assets):
    collection = bpy.data.collections.new("ZooAnimals")
    bpy.context.scene.collection.children.link(collection)
    count = 0
    for feature in features:
        rule = PLACEMENTS.get(str(feature["id"]))
        if not rule:
            continue
        asset_id, copies = rule
        x, y = feature["center"]
        configs = [((-2, 0), 1.6), ((6, 3), 1.3)]
        for index in range(copies):
            offset, scale = configs[index]
            obj = assets[asset_id].copy()
            obj.data = assets[asset_id].data
            obj.name = f"Animal.{asset_id}.{feature['id']}.{index + 1}"
            obj.location = (x + offset[0], y + offset[1], .30)
            obj.scale = (scale, scale, scale)
            obj.hide_render = False
            obj.hide_viewport = False
            # Stable three-quarter presentation instead of random rotations.
            angle_seed = (int(feature["id"][-4:]) + index * 137) % 1000
            obj.rotation_euler[2] = -.72 + angle_seed / 1000 * 1.44
            collection.objects.link(obj)
            obj.hide_set(False)
            count += 1
    if count != 29:
        raise RuntimeError(f"Expected 29 animal instances, generated {count}")
    return collection


def render_contact_sheet(root, assets):
    scene = bpy.data.scenes.new("AnimalPreview")
    scene.world = bpy.data.worlds.new("AnimalPreviewWorld")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs[0].default_value = (1, 1, 1, 1)
    background.inputs[1].default_value = .38
    collection = bpy.data.collections.new("AnimalPreview")
    scene.collection.children.link(collection)

    columns = 7
    for index, asset_id in enumerate(ASSETS):
        row, column = divmod(index, columns)
        obj = assets[asset_id].copy()
        obj.data = assets[asset_id].data
        obj.name = f"Preview.{asset_id}"
        obj.hide_render = False
        obj.hide_viewport = False
        obj.location = ((column - 3) * 3.25, 0, (2 - row) * 5.25)
        obj.scale = (.70, .70, .70)
        collection.objects.link(obj)

    camera_data = bpy.data.cameras.new("AnimalPreviewCamera")
    camera = bpy.data.objects.new("AnimalPreviewCamera", camera_data)
    collection.objects.link(camera)
    camera.location = (0, -42, 7.2)
    camera.rotation_euler = ((Vector((0, 0, 7.2)) - camera.location).to_track_quat("-Z", "Y").to_euler())
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 26
    scene.camera = camera

    for name, kind, location, energy, size in [
        ("Key", "AREA", (-8, -10, 18), 850, 12),
        ("Fill", "AREA", (10, -5, 10), 450, 10),
    ]:
        data = bpy.data.lights.new(name, kind)
        data.energy, data.shape, data.size = energy, "DISK", size
        light = bpy.data.objects.new(name, data)
        light.location = location
        light.rotation_euler = ((Vector((0, 0, 6)) - light.location).to_track_quat("-Z", "Y").to_euler())
        collection.objects.link(light)

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 2100, 1050
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = str(Path(root) / "blender" / "animals-preview.png")
    bpy.context.window.scene = scene
    bpy.ops.render.render(write_still=True)
    return scene


def select_main_export_objects(scene, library):
    bpy.context.window.scene = scene
    bpy.ops.object.select_all(action="DESELECT")
    library_objects = set(library.objects)
    for obj in scene.objects:
        if obj.type == "MESH" and obj not in library_objects:
            obj.hide_set(False)
            obj.select_set(True)
