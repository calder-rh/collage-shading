from pathlib import Path
from pymel.core import *


shading_dir = Path(workspace(q=True, rd=True)) / 'shading'

def shading_path(*args):
    return shading_dir / Path(*args)

def relative_path(path):
    return Path(path).relative_to(shading_dir.parent)
