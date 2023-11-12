import sys
import importlib
from pymel.core import *
from pathlib import Path
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import subprocess
from internals import network, shading_path, surface_values, coordinate_converter, palettes, collage_shader, world_placement, screen_placement, tracking_projection, dialog_with_support
importlib.reload(network)
importlib.reload(shading_path)
importlib.reload(collage_shader)
importlib.reload(tracking_projection)
importlib.reload(coordinate_converter)
importlib.reload(surface_values)
importlib.reload(palettes)
importlib.reload(world_placement)
importlib.reload(screen_placement)
importlib.reload(dialog_with_support)
from internals.dialog_with_support import dialog_with_support
from internals.shading_path import shading_path
from internals.surface_values import calculate_surface_values
from internals.collage_shader import CollageShader
from pathlib import Path
from hashlib import md5
import json
from shutil import rmtree


selection = ls(sl=True)
if not selection:
    confirmDialog(t='Error', m='Please select at least one object.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
    exit()

dialog_output = fileDialog2(fm=1, cap='Choose map', okc='Create shader', dir=shading_path('maps'))
if dialog_output is None:
    exit()
map_image_path = Path(dialog_output[0])

image_hash = md5(map_image_path.read_bytes()).hexdigest()

map_dir_path = map_image_path.with_name(map_image_path.stem)
map_data_path = map_dir_path / 'map data.json'
masks_path = map_dir_path / 'masks'

if map_data_path.exists():
    with map_data_path.open() as file:
        original_map_data = json.load(file)
    if original_map_data['hash'] == image_hash:
        map_data_status = 'up to date'
    else:
        map_data_status = 'out of date'
else:
    map_data_status = 'nonexistent'

if not map_dir_path.exists():
    map_dir_path.mkdir()

if map_data_status != 'up to date':
    map_proc = subprocess.run(['python3', shading_path('code', 'internals', 'map_data.py'), map_image_path, map_data_path], capture_output=True)
    if map_proc.returncode or (err := map_proc.stderr.decode("utf-8")) != '':
        err = map_proc.stderr.decode("utf-8")
        if '\n' in err:
            title, msg = err.split('\n', maxsplit=1)
        else:
            title = 'Error'
            msg = err
        dialog_output = dialog_with_support(title, msg, ['I’ll fix it'], cb='I’ll fix it', db='I’ll fix it', icon='warning')
        if map_data_status == 'nonexistent':
            map_data_path.unlink(missing_ok=True)
        exit()

with map_data_path.open() as file:
    map_data = json.load(file)

map_data['hash'] = image_hash

if map_data['anti-aliasing warning']:
    msg = 'It looks like you may have used a brush with anti-aliasing, which produces many colors along the edge of a stroke. If that is the case and you make a shader based on this map, each of those different colors along the edge will become its own facet. Do you still want to continue?'
    dialog_output = dialog_with_support('Wait', msg, ['No', 'Yes'], cb='No', db='Yes', icon='question')
    if dialog_output in ['No', 'dismiss']:
        map_data_path.unlink()
        exit()
    else:
        map_data['anti-aliasing warning'] = False

facet_borders_changed = map_data_status != 'nonexistent' and original_map_data['pixels'] != map_data['pixels']
blur_markers_changed = map_data_status != 'nonexistent' and [facet['blur markers'] for facet in original_map_data['facets'].values()] != [facet['blur markers'] for facet in map_data['facets'].values()]

num_facets = len(map_data['facets'])
if num_facets > 1 and (not masks_path.exists() or facet_borders_changed or blur_markers_changed):
    if masks_path.exists():
        rmtree(masks_path)
    promptDialog(t='Enter Resolution', m='Enter the resolution for the blur mask images. Larger values take longer to run.', b=['OK'], ma='left', st='integer', tx='256')
    blur_resolution = int(promptDialog(q=True, tx=True))
    node = None
    for node in selection:
        if node.type() == 'mesh':
            obj = node.getTransform()
            break
        elif node.type() == 'transform' and node.getShape().type() == 'mesh':
            obj = node
            break
    if node is None:
        dialog_with_support('Error', 'Please select at least one mesh.', ['OK'], cb='OK', db='OK', icon='warning')
    if node.type() == 'mesh':
        obj = node.getTransform()
    elif node.type() == 'transform' and node.getShape().type() == 'mesh':
        obj = node
    surface_values_path = calculate_surface_values(obj, map_data_path, blur_resolution)
    blur_proc = subprocess.run(['python3', shading_path('code', 'internals', 'blur_images.py'), surface_values_path, map_data_path], capture_output=True)

with map_data_path.open('w') as file:
    json.dump(map_data, file, indent=4)

for node in selection:
    if node.type() == 'mesh':
        obj = node.getTransform()
    elif node.type() == 'transform' and node.getShape().type() == 'mesh':
        obj = node
    else:
        continue
    CollageShader({'object': obj.name()}, obj, map_image_path)
