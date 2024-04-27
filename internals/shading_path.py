from pathlib import Path
from os import sep


this_file = Path(__file__)
shading_dir = this_file.parents[2]

def shading_path(*args):
    return shading_dir / Path(*args)

def relative_path(path):
    return Path(path).relative_to(shading_dir.parent)

def relative_path_string(path):
    return './' + str(relative_path(path))
