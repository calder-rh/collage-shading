from pymel.core import *

import importlib
from internals import network, shading_path, global_controls, surface_values, coordinate_converter, palettes, collage_shader, world_placement, screen_placement, tracking_projection, dialog_with_support, unique_name
importlib.reload(network)
importlib.reload(shading_path)
importlib.reload(global_controls)
importlib.reload(surface_values)
importlib.reload(coordinate_converter)
importlib.reload(palettes)
importlib.reload(collage_shader)
importlib.reload(world_placement)
importlib.reload(screen_placement)
importlib.reload(tracking_projection)
importlib.reload(dialog_with_support)
importlib.reload(unique_name)

from internals.dialog_with_support import dialog_with_support
from internals.shading_path import shading_path
from internals.surface_values import calculate_surface_values
from internals.collage_shader import CollageShader
from internals.unique_name import format_unique_name

from pathlib import Path
from shutil import rmtree
import json
import subprocess
from enum import Enum


shell_name = subprocess.run('echo $SHELL', capture_output=True, shell=True).stdout.decode('utf-8').strip().split('/')[-1]
interpreter = subprocess.run(f'source ~/.{shell_name}rc; which python3', capture_output=True, shell=True).stdout.decode('utf-8').strip()
if not interpreter:
    interpreter = 'python3'

class MapDataStatus(Enum):
    nonexistent = 0
    up_to_date = 1
    out_of_date = 2


def run():
    selection = ls(sl=True)
    if not selection:
        confirmDialog(t='Error', m='Please select at least one object.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()

    dialog_output = fileDialog2(fm=1, cap='Choose map', okc='Create shader', dir=shading_path('maps'))
    if dialog_output is None:
        exit()
    map_image_path = Path(dialog_output[0])

    image_modification_time = map_image_path.stat().st_mtime

    map_dir_path = map_image_path.with_name(map_image_path.stem)
    map_data_path = map_dir_path / 'map data.json'
    masks_path = map_dir_path / 'masks'

    if map_data_path.exists():
        with map_data_path.open() as file:
            original_map_data = json.load(file)
        if original_map_data['last modified'] == image_modification_time:
            map_data_status = MapDataStatus.up_to_date
        else:
            map_data_status = MapDataStatus.out_of_date
    else:
        map_data_status = MapDataStatus.nonexistent

    if not map_dir_path.exists():
        map_dir_path.mkdir()

    if map_data_status != MapDataStatus.up_to_date:
        map_proc = subprocess.run([interpreter, shading_path('code', 'internals', 'map_data.py'), map_image_path, map_data_path], capture_output=True)
        if map_proc.returncode or (err := map_proc.stderr.decode("utf-8")) != '':
            err = map_proc.stderr.decode("utf-8")
            if '\n' in err:
                title, msg = err.split('\n', maxsplit=1)
            else:
                title = 'Error'
                msg = err
            dialog_output = dialog_with_support(title, msg, ['I’ll fix it'], cb='I’ll fix it', db='I’ll fix it', icon='warning')
            if map_data_status == MapDataStatus.nonexistent:
                map_data_path.unlink(missing_ok=True)
            exit()

        with map_data_path.open() as file:
            new_map_data = json.load(file)

        new_map_data['last modified'] = image_modification_time

        if new_map_data['anti-aliasing warning']:
            msg = 'It looks like you may have used a brush with anti-aliasing, which produces many colors along the edge of a stroke. If that is the case and you make a shader based on this map, each of those different colors along the edge will become its own facet. Do you still want to continue?'
            dialog_output = dialog_with_support('Wait', msg, ['No', 'Yes'], cb='No', db='Yes', icon='question')
            if dialog_output in ['No', 'dismiss']:
                map_data_path.unlink()
                exit()
            else:
                new_map_data['anti-aliasing warning'] = False

    facet_borders_changed = map_data_status == MapDataStatus.nonexistent or (map_data_status == MapDataStatus.out_of_date and ((('pixels' in original_map_data) != ('pixels' in new_map_data)) or ('pixels' in original_map_data and 'pixels' in new_map_data and original_map_data['pixels'] != new_map_data['pixels'])))
    blur_markers_changed = map_data_status == MapDataStatus.nonexistent or (map_data_status == MapDataStatus.out_of_date and [facet['blur markers'] for facet in original_map_data['facets'].values()] != [facet['blur markers'] for facet in new_map_data['facets'].values()])

    surface_values_path = map_dir_path / 'surface values.json'
    masks_exist = masks_path.exists() and any(file.suffix == '.png' for file in masks_path.iterdir())
    surface_values_exist = surface_values_path.exists()

    if map_data_status == MapDataStatus.up_to_date:
        num_facets = len(original_map_data['facets'])
    else:
        num_facets = len(new_map_data['facets'])

    if num_facets > 1 and (not (masks_exist or surface_values_exist) or facet_borders_changed or blur_markers_changed):
        if masks_exist:
            rmtree(masks_path, ignore_errors=True)

        dialog_output = promptDialog(t='Enter resolution', m='Enter the resolution for the facet mask images. Larger values take longer to run.', b=['OK'], ma='left', st='integer', tx='256')
        if dialog_output == 'dismiss':
            exit()
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
    
    if num_facets > 1 and not masks_exist:
        blur_proc = subprocess.run([interpreter, shading_path('code', 'internals', 'blur_images.py'), surface_values_path], capture_output=True)

    if map_data_status != MapDataStatus.up_to_date:
        with map_data_path.open('w') as file:
            json.dump(new_map_data, file, indent=4)

    for node in selection:
        if node.type() == 'mesh':
            obj = node.getTransform()
        elif node.type() == 'transform' and node.getShape().type() == 'mesh':
            obj = node
        else:
            continue
        CollageShader({'mesh': format_unique_name(obj)}, obj, map_image_path)
