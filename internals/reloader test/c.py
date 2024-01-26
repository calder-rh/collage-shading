from a import aa
import b
import hmm.d
# c = aa + b.bb

# import sys
# from importlib import reload
# module_path_to_module = {spec.origin: module for module in sys.modules.values() if (spec := module.__spec__)}
# from reloader import ordered_modules
# for module_path in ordered_modules():
#     reload(module_path_to_module[module_path])

import sys
from reloader import ordered_modules

ordered_modules(sys.modules)