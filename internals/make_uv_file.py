from pymel.core import *

from internals.shading_path import shading_path

import sys, subprocess


def make_uv_file(name, resolution):
    path = shading_path('maps', name + ' UVs.png')
    if path.exists():
        confirmDialog(t='Error', m='There is already a file with that name.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()
    uvSnapshot(ff='png', xr=resolution, yr=resolution, r=127, g=127, b=127, n=path, o=True)
    abspath = str(path.absolute())
    if sys.platform == 'darwin':
        subprocess.run(['open', '-R', abspath])
    elif sys.platform == 'win32':
        subprocess.run(fr'explorer /select,"C:{abspath}"')


def prompt_creation(name):
    window()
    formLayout()

    if window("map_prompt_window", exists=True):
        deleteUI("map_prompt_window")

    prompt_window = window("map_prompt_window", title="Set up map", widthHeight=(300, 150))
    main_layout = formLayout()

    # Name Label and Text Field
    map_name_label = text(label="Name")
    map_name_field = textField(text=name)

    # Resolution Label and Numeric Field
    resolution_label = text(label="Resolution")
    resolution_field = intField(value=1024)

    def onCreate(*args):
        # Get the values from the input fields
        name = textField(map_name_field, query=True, text=True)
        resolution = intField(resolution_field, query=True, value=True)

        make_uv_file(name, resolution)

        # Close the window
        deleteUI("map_prompt_window")

    def onCancel(*args):
        deleteUI("map_prompt_window")

    # Create and Cancel Buttons
    create_button = button(label="Create", command=onCreate)
    cancel_button = button(label="Cancel", command=onCancel)

    # Arrange the elements in a formLayout
    formLayout(main_layout, edit=True,
        attachForm=[
            (map_name_label, 'top', 14),
            (map_name_label, 'left', 10),
            (map_name_field, 'top', 10),
            (resolution_label, 'left', 10),
            (resolution_label, 'top', 44),
            (map_name_field, 'right', 10),
            (resolution_field, 'right', 10),
            (resolution_field, 'top', 40),
            (create_button, 'bottom', 10),
            (cancel_button, 'bottom', 10),
            (create_button, 'right', 10)
        ],
        attachControl=[
            (map_name_field, 'left', 10, map_name_label),
            (resolution_field, 'left', 10, resolution_label),  
            (cancel_button, 'right', 10, create_button)
        ]
    )

    showWindow(prompt_window)


def run():
    selection = ls(sl=True)
    if not selection:
        confirmDialog(t='Error', m='Please select an object.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()
    if len(selection) > 1:
        confirmDialog(t='Error', m='Please only select one object.', b='OK', cb='OK', db='OK', icon='warning', ma='left')
        exit()
    selected_obj = selection[0]
    selection_name = selected_obj.name()

    prompt_creation(selection_name)
