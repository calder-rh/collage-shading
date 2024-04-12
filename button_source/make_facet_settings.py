from pymel.core import *

import importlib
from internals import shading_path, utilities
importlib.reload(shading_path)
importlib.reload(utilities)
from internals.utilities import show_file
from internals.shading_path import shading_path

from pathlib import Path
import json


def run():
    dialog_output = fileDialog2(fm=1, cap='Choose palette', okc='Create settings', dir=shading_path('palettes'))
    if dialog_output is None:
        exit()
    
    output_path = Path(dialog_output[0]).relative_to(shading_path())
    file_contents = {
        'palette': str(output_path),
        'scale': 1,
        'object up': (0, 1, 0),
        'image up': 0,
        'edge distance': (0.1, 0.1)
    }

    i = 1
    while True:
        if i == 1:
            candidate_name = 'facet settings.json'
        else:
            candidate_name = f'facet settings {i}.json'
        candidate_path = output_path.parent / candidate_name
        if not candidate_path.exists():
            break
        i += 1

    settings_path = candidate_path
    with settings_path.open('w') as file:
        json.dump(file_contents, file, indent=4)
    
    show_file(settings_path)
