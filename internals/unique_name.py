from pymel.core import *


def unique_name(obj):
    parents = [obj]
    while (next_parent := parents[0].getParent()) is not None:
        parents.insert(0, next_parent)
    names = [item.name() for item in parents]
    return '_'.join(names)