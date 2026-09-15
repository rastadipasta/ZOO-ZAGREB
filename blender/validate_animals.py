"""Validate generated standalone animal GLBs and their main-map instances."""
import pathlib
import sys

import bpy

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
import animals


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


animal_dir = ROOT / "public" / "models" / "animals"
files = sorted(animal_dir.glob("*.glb"))
expected = {f"{asset_id}.glb" for asset_id in animals.ASSETS}
actual = {path.name for path in files}
assert actual == expected, f"Animal GLB set mismatch: missing={expected-actual}, extra={actual-expected}"

for path in files:
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    assert len(meshes) == 1, f"{path.name}: expected one joined mesh, found {len(meshes)}"
    mesh = meshes[0]
    assert len(mesh.data.vertices) > 0, f"{path.name}: empty mesh"
    min_z = min((mesh.matrix_world @ vertex.co).z for vertex in mesh.data.vertices)
    assert abs(min_z) < .002, f"{path.name}: feet are not on Z=0 ({min_z})"
    assert mesh.data.materials, f"{path.name}: no materials"

clear_scene()
main_glb = ROOT / "public" / "models" / "zoo-zagreb.glb"
bpy.ops.import_scene.gltf(filepath=str(main_glb))
instances = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith("Animal.")]
assert len(instances) == 29, f"Expected 29 map animal instances, found {len(instances)}"
found_assets = {obj.name.split(".")[1] for obj in instances}
assert found_assets == set(animals.ASSETS), f"Main GLB asset mismatch: {found_assets ^ set(animals.ASSETS)}"
assert main_glb.stat().st_size <= 6_000_000, f"Main GLB exceeds 6 MB: {main_glb.stat().st_size}"
print(f"VALID: {len(files)} standalone animal GLBs, {len(instances)} map instances, {main_glb.stat().st_size} byte main GLB")
