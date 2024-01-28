from pymel.core import *

from internals.network import Network
from internals.global_controls import gcn
import math


class GroundUVConverter(Network):
    relevant_context = []

    def __init__(self, _):
        xyz_to_uv_calculator = self.utility('closestPointOnMesh', 'xyz_to_uv_calculator')
        result = xyz_to_uv_calculator.result
        gcn.ground_mesh.connect(xyz_to_uv_calculator.inMesh)
        self.xyz_in = xyz_to_uv_calculator.inPosition
        self.u_out = result.parameterU
        self.v_out = result.parameterV


millimeters_per_inch = 25.4

def sy_to_uv(y_interp, time):
    camera_trans = listConnections(gcn.camera_message, s=True, d=False)[0]
    camera_shape = camera_trans.getShape()

    camera_tx = camera_trans.tx.get(t=time)
    camera_ty = camera_trans.ty.get(t=time)
    camera_tz = camera_trans.tz.get(t=time)
    camera_rx = camera_trans.rx.get(t=time)
    camera_ry = camera_trans.ry.get(t=time)
    ground_y = gcn.ground_y.get(t=time)
    vertical_aperture = millimeters_per_inch * camera_shape.horizontalFilmAperture.get() / gcn.camera.aspect_ratio.get()
    focal_length = camera_shape.focalLength.get(t=time)

    horizon_screen_y = focal_length * math.tan(-math.radians(camera_rx)) / vertical_aperture
    screen_y_min = -0.5
    screen_y_max = min(0.5, horizon_screen_y)
    screen_y = screen_y_min + (screen_y_max - screen_y_min) * y_interp

    angle = camera_rx + math.degrees(math.atan(screen_y * vertical_aperture / focal_length))
    flat_distance = (camera_ty - ground_y) / math.tan(math.radians(angle))
    flat_x = camera_tx + flat_distance * math.sin(math.radians(camera_ry))
    flat_y = ground_y
    flat_z = camera_tz + flat_distance * math.cos(math.radians(camera_ry))

    return flat_x, flat_y, flat_z