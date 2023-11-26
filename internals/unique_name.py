from pymel.core import *
import re


def format_unique_name(obj):
    return re.sub('^_', 'S_', obj.name().replace('|', '_'))