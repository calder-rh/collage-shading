from pymel.core import *


def unique_name(obj):
    return obj.name().replace('|', '_')