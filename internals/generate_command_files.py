from pathlib import Path

template = """from pymel.core import *
import sys, importlib
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

from internals.buttons import {filename}
importlib.reload({filename})
from internals.buttons import {filename}
{filename}.run()
"""

buttons_dir = Path(__file__).parent / 'buttons'
python_files = [item for item in buttons_dir.iterdir() if item.is_file() and item.suffix == '.py']

for file in python_files:
    outer_file = Path(__file__).parents[1] / file.name
    contents = template.format(filename = file.stem)
    outer_file.write_text(contents)
