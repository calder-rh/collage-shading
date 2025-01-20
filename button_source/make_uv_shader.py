from pymel.core import *

import importlib
from internals import (
    network,
    shading_path,
    global_controls,
    palettes,
    dialog_with_support,
    utilities,
    uv_shader,
)

importlib.reload(network)
importlib.reload(shading_path)
importlib.reload(global_controls)
importlib.reload(palettes)
importlib.reload(dialog_with_support)
importlib.reload(utilities)
importlib.reload(uv_shader)

from internals.shading_path import shading_path
from internals import palettes
from internals.dialog_with_support import dialog_with_support
from internals.uv_shader import UVShader
from internals.utilities import format_unique_name


def run():
    selection = ls(sl=True)
    if not selection:
        confirmDialog(
            t="Error",
            m="Please select at least one object.",
            b="OK",
            cb="OK",
            db="OK",
            icon="warning",
            ma="left",
        )
        exit()

    dialog_output = fileDialog2(
        fm=1, cap="Choose palette", okc="Create shader", dir=shading_path("palettes")
    )
    if dialog_output is None:
        exit()
    palette_path = dialog_output[0]

    if not palettes.is_valid_selection(palette_path):
        error_message = "Please select a file or folder that has a valid palette path."
        dialog_with_support(
            "Error", error_message, "OK", cb="OK", db="OK", icon="warning"
        )
        exit()

    for node in selection:
        if node.type() == "mesh":
            obj = node.getTransform()
        elif node.type() == "transform" and node.getShape().type() == "mesh":
            obj = node
        else:
            continue
        UVShader({"mesh": format_unique_name(obj)}, obj, palette_path)
