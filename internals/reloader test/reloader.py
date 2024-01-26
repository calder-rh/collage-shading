# import types
# import inspect


# import ast


# import c
# print(sys.modules.keys())

# import types
# def imports():
#     for name, val in globals().items():
#         if isinstance(val, types.ModuleType):
#             yield val.__name__

# print(list(imports()))


# mf = ModuleFinder()
# mf.run_script(c.__file__)
# for k, v in mf.modules.items():
#     print(k)
#     print('   ', v)

# def reload_modules():
#     caller_frame = inspect.currentframe().f_back
#     caller_globals = caller_frame.f_globals
#     modules = [e for e in caller_globals.values() if isinstance(e, types.ModuleType) and e.__name__ not in ['builtins', 'reloader']]
    
#     dependencies = {}
#     mf = ModuleFinder()
#     for module in modules:
#         print(module.__name__)
#         mf.run_script(module.__file__)
#         dependencies[module] = {dep for dep in mf.modules.values() if dep != module and dep.__name__ != '__main__'}

#     print(dependencies)

# import c
# import pkgutil
# print(list(pkgutil.iter_modules(c.__file__)))

import ast
from importlib import reload
import inspect
from modulefinder import ModuleFinder
import importlib, importlib.util
from graphlib import TopologicalSorter

# def get_imports(file_path):
#     with open(file_path, 'r') as file:
#         tree = ast.parse(file.read(), filename=file_path)

#     imports = []
#     for node in ast.walk(tree):
#         if isinstance(node, ast.Import):
#             imports.extend(alias.name for alias in node.names)
#         elif isinstance(node, ast.ImportFrom):
#             imports.append(node.module)

#     return imports

def ordered_modules(sys_modules):
    caller_frame = inspect.currentframe().f_back
    file_path = caller_frame.f_code.co_filename

    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports |= {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
    
    imports.discard('reloader')

    dependencies = {}
    path_to_module = {}
    for module_name in imports:
        module_spec = importlib.util.find_spec(module_name)
        module_path = module_spec.origin
        path_to_module[module_path] = importlib.util.module_from_spec(module_spec)
        mf = ModuleFinder()
        try:
            mf.run_script(module_path)
            dependencies[module_path] = {dep.__file__ for dep in mf.modules.values() if dep.__name__ != '__main__'}
        except:
            continue

    sorter = TopologicalSorter(dependencies)
    ordered_module_paths = sorter.static_order()

    sys_module_path_to_module = {spec.origin: module for module in sys_modules.values() if (spec := module.__spec__)}
    for module_path in ordered_module_paths:
        reload(sys_module_path_to_module[module_path])

