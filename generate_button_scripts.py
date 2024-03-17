from pathlib import Path

template = """from pymel.core import *
import sys, importlib
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

from button_source import {filename}
importlib.reload({filename})
from button_source import {filename}
{filename}.run()
"""

buttons_dir = Path(__file__).parent / 'button_source'
python_files = [item for item in buttons_dir.iterdir() if item.is_file() and item.suffix == '.py' and item.stem != 'system_check']

for source_file in python_files:
    script_file = Path(__file__).parent / 'button_scripts' / source_file.name
    contents = template.format(filename = source_file.stem)
    script_file.write_text(contents)
