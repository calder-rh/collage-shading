import sys
import importlib
from pymel.core import *
from pathlib import Path
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import subprocess, webbrowser
from internals import network, shading_path, surface_values, coordinate_converter, palettes, collage_shader, world_placement, screen_placement, tracking_projection
importlib.reload(network)
importlib.reload(shading_path)
importlib.reload(collage_shader)
importlib.reload(tracking_projection)
importlib.reload(coordinate_converter)
importlib.reload(surface_values)
importlib.reload(palettes)
importlib.reload(world_placement)
importlib.reload(screen_placement)
from internals.shading_path import shading_path
from internals.surface_values import calculate_surface_values
from internals.collage_shader import CollageShader
from pathlib import Path
import json


selection = ls(sl=True)
if not selection:
    confirmDialog(t='Error', m='Please select at least one object.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
    exit()

dialog_output = fileDialog2(fm=1, cap='Choose map', okc='Create shader', dir=shading_path('maps'))
if dialog_output is None:
    exit()
map_image_path = Path(dialog_output[0])

map_dir_path = map_image_path.with_name(map_image_path.stem)
map_data_path = map_dir_path / 'map data.json'
masks_path = map_dir_path / 'masks'

new_map_data = not map_data_path.exists()

if not map_dir_path.exists():
    map_dir_path.mkdir()

def dialog_with_support(title, msg, buttons, **kwargs):
    dialog_output = confirmDialog(t=title, m=msg, b=['What?'] + buttons, ma='left', **kwargs)
    if dialog_output == 'What?':
        webbrowser.open('slack://channel?id=C05BFV55GLT&team=T05B9C5MHKQ')
        dialog_output = confirmDialog(t='Would you like to copy the error message to your clipboard?', m=title + '\n' + msg, b=['Yes', 'No'], cb='No', db='Yes', icon='question', ma='left')
        if dialog_output == 'Yes':
            if sys.platform == 'darwin':
                copy_keyword = 'pbcopy'
            elif sys.platform == 'win32':
                copy_keyword = 'clip'
            subprocess.run(copy_keyword, universal_newlines=True, input=title + '\n' + msg)
        exit()
    else:
        return dialog_output

if new_map_data:
    map_proc = subprocess.run(['python3', shading_path('code', 'internals', 'map_data.py'), map_image_path, map_data_path], capture_output=True)
    if map_proc.returncode or (err := map_proc.stderr.decode("utf-8")) != '':
        err = map_proc.stderr.decode("utf-8")
        if '\n' in err:
            title, msg = err.split('\n', maxsplit=1)
        else:
            title = 'Error'
            msg = err
        dialog_output = dialog_with_support(title, msg, ['I’ll fix it'], cb='I’ll fix it', db='I’ll fix it', icon='warning')
        map_data_path.unlink(missing_ok=True)
        exit()

with map_data_path.open() as file:
    map_data = json.load(file)

if map_data['anti-aliasing warning']:
    msg = 'It looks like you may have used a brush with anti-aliasing, which produces many colors along the edge of a stroke. If that is the case and you make a shader based on this map, each of those different colors along the edge will become its own facet. Do you still want to continue?'
    dialog_output = dialog_with_support('Wait', msg, ['No', 'Yes'], cb='No', db='Yes', icon='question')
    if dialog_output in ['No', 'dismiss']:
        map_data_path.unlink()
        exit()

num_facets = len(map_data['facets'])
if num_facets > 1:
    if new_map_data:
        promptDialog(t='Enter Resolution', m='Enter the resolution for the blur mask images. Larger values take longer to run.', b=['OK'], ma='left', st='integer', tx='256')
        blur_resolution = promptDialog(q=True, tx=True)
        map_data['blur resolution'] = int(blur_resolution)
        with map_data_path.open('w') as file:
            json.dump(map_data, file, indent=4)

    if not masks_path.exists():
        node = selection[0]
        if node.type() == 'mesh':
            obj = node.getTransform()
        elif node.type() == 'transform' and node.getShape().type() == 'mesh':
            obj = node
        surface_values_path = calculate_surface_values(obj, map_data_path)
        blur_proc = subprocess.run(['python3', shading_path('code', 'internals', 'blur_images.py'), surface_values_path, map_data_path], capture_output=True)
        print('*' * 30, blur_proc.stdout, blur_proc.stderr)
else:
    if 'blur resolution' in map_data:
        del map_data['blur resolution']
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
