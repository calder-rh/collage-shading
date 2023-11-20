from pymel.core import *
import re


def unique_name(obj):
    return re.sub('^_', 'S_', obj.name().replace('|', '_'))