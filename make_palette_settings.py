import sys, subprocess
import importlib
from pymel.core import *
code_path = workspace.getcwd() / 'shading' / 'fantasy' / 'code'
if code_path not in sys.path:
    sys.path.append(code_path)

from internals import palettes
importlib.reload(palettes)
from internals import palettes
from internals.shading_path import shading_path


dialog_output = fileDialog2(fm=1, cap='Choose palette', okc='Make settings file', dir=shading_path('palettes'))
if dialog_output is None:
    exit()
palette_path = dialog_output[0]

if not palettes.is_valid_selection(palette_path):
    error_message = 'Please select a file or folder that has a valid palette path.'
    confirmDialog(t='Error', m=error_message, b='OK', cb='OK', db='OK', icon='warning', ma='left')
    exit()

palette = palettes.get_palette(palette_path)
palette.make_settings_file()
settings_path = palette.settings_path

import sys, subprocess
abspath = str(settings_path.absolute())
if sys.platform == 'darwin':
    subprocess.run(['open', '-R', abspath])
elif sys.platform == 'win32':
    subprocess.run(fr'explorer /select,"C:{abspath}"')
