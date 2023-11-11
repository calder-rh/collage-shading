from pymel.core import *
from random import uniform, choice

import sys, importlib, os

from shading_path import shading_path


import tracking_projection, screen_placement, world_placement, shading_controller, network
importlib.reload(network)
importlib.reload(shading_controller)
importlib.reload(world_placement)
importlib.reload(screen_placement)
importlib.reload(tracking_projection)
import world_placement, screen_placement, shading_controller, tracking_projection

owp = world_placement.ObjWorldPlacement({'object': 'cyl'}, SCENE.pCylinder1)
sp = screen_placement.ScreenPlacement({'facet': 'test'}, owp.center_ws, owp.rotation_ws, 0)
fi = tracking_projection.FacetImage(shading_path('textures/calibration.png'), 0, 0, 0, 5)
tp = tracking_projection.TrackingProjection({'facet': 'test', 'image': 'calibration'}, sp, fi)
# sc = shading_controller.ShadingController({})
