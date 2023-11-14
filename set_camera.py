from pymel.core import *
import sys
from pathlib import Path
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network, shading_controller
importlib.reload(network)
importlib.reload(shading_controller)

from internals import set_camera
set_camera.run()