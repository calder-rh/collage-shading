from pathlib import Path
from pymel.core import *


this_file = Path(__file__)
shading_dir = this_file.parents[2]

def shading_path(*args):
    return Path(workspace(q=True, rd=True)) / 'shading' / Path(*args)

def relative_path(path):
    return Path(path).relative_to(shading_dir.parent)
