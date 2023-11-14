from pymel.core import *
import sys
from pathlib import Path
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import shading_path, palettes, dialog_with_support
importlib.reload(shading_path)
importlib.reload(palettes)
importlib.reload(dialog_with_support)

from internals import make_palette_settings
make_palette_settings.run()