import importlib
from pymel.core import *

from internals import palettes, dialog_with_support
importlib.reload(palettes)
importlib.reload(dialog_with_support)
from internals import palettes
from internals.shading_path import shading_path
from internals.dialog_with_support import dialog_with_support


def run():
    dialog_output = fileDialog2(fm=1, cap='Choose palette', okc='Make settings file', dir=shading_path('palettes'))
    if dialog_output is None:
        exit()
    palette_path = dialog_output[0]

    if not palettes.is_valid_selection(palette_path):
        error_message = 'Please select a file or folder that has a valid palette path.'
        dialog_with_support('Error', error_message, 'OK', cb='OK', db='OK', icon='warning')
        exit()

    gradient = palettes.is_gradient(palette_path)
    if gradient:
        dialog_output = promptDialog(t='Enter the number of shades', m='Choose how many shades should be drawn from this gradient image.', b=['OK', 'Cancel'], db='OK', cb='Cancel', ma='left', st='integer', tx=str(palettes.default_num_shades))
        if dialog_output in ['Cancel', 'dismiss']:
            exit()
        num_shades = int(promptDialog(q=True, tx=True))
    palette = palettes.get_palette(palette_path)
    if gradient:
        palette.make_settings_file(num_shades=num_shades)
    else:
        palette.make_settings_file()
    settings_path = palette.settings_path

    import sys, subprocess
    abspath = str(settings_path.absolute())
    if sys.platform == 'darwin':
        subprocess.run(['open', '-R', abspath])
    elif sys.platform == 'win32':
        subprocess.run(fr'explorer /select,"C:{abspath}"')
