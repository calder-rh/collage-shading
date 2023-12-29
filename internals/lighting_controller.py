from pymel.core import *
from internals.network import Network

from internals.control_groups import ControlGroups
from internals.invisible import make_invisible_in_render
from internals.sun_pair import SunPair, SunPairShaders
from internals.shading_controller import ShadingController


class LightingController(Network):
    relevant_context = []
    prefix = ''
    delete = False

    def __init__(self, _):
        is_new = not objExists('lighting_controller')

        cg = ControlGroups({})

        lighting_controller_trans, _ = self.poly(polyCube, 'lighting_controller')
        setAttr(lighting_controller_trans.r, l=True)
        lighting_controller_shape = lighting_controller_trans.getShape()
        make_invisible_in_render(lighting_controller_shape)
        parent(lighting_controller_trans, cg.shading_controls)

        if is_new:
            light_direction_cone_trans, _ = self.poly(polyCone, 'light_direction_cone', radius=0.4, height=4, heightBaseline=-1, axis=(0, 0, 1))
            light_source_ball_trans, _ = self.poly(polySphere, 'light_source_ball', radius=0.2, axis=(0, 0, 1))
            light_source_ball_trans.tz.set(3.9)
            light_direction_trans, _ = polyUnite(light_direction_cone_trans, light_source_ball_trans, n='light_direction')
            light_direction_shape = light_direction_trans.getShape()
            delete(light_direction_trans, ch=True)

            initial_sg_connection = listConnections(light_direction_shape, s=False, c=True, p=True)[0]
            initial_sg_connection[0] // initial_sg_connection[1]
            sun_sg = SunPairShaders({}).sun_sg
            sets(sun_sg, e=True, fe=light_direction_shape)
            parent(light_direction_trans, lighting_controller_trans)
            setAttr(light_direction_trans.t, l=True)
            setAttr(light_direction_trans.s, l=True)
            make_invisible_in_render(light_direction_shape)
        else:
            light_direction_trans = PyNode('light_direction')

        lc = lighting_controller_trans

        if is_new:
            addAttr(lc, ln='sun_distance', min=0, smx=1000, dv=100)

            addAttr(lc, ln='front_value_range', at='compound', nc=2)
            addAttr(lc, p='front_value_range', ln='front_min', min=0, max=1, dv=0)
            addAttr(lc, p='front_value_range', ln='front_max', min=0, max=1, dv=1)

            addAttr(lc, ln='back_value_range', at='compound', nc=2)
            addAttr(lc, p='back_value_range', ln='back_min', min=0, max=1, dv=0.3)
            addAttr(lc, p='back_value_range', ln='back_max', min=0, max=1, dv=0.7)
            
            addAttr(lc, ln='atmospheric_perspective', at='compound', nc=3)
            addAttr(lc, p='atmospheric_perspective', ln='enable', at='bool')
            addAttr(lc, p='atmospheric_perspective', ln='half_distance', min=1, smx=1000, dv=100)
            addAttr(lc, p='atmospheric_perspective', ln='color', at='float3', uac=True)
            addAttr(lc, ln='colorR', at='float', parent='color')
            addAttr(lc, ln='colorG', at='float', parent='color')
            addAttr(lc, ln='colorB', at='float', parent='color')
            lighting_controller_trans.atmospheric_perspective.color.set(0.5, 0.7, 1)

        sc = ShadingController()
        
        lc.sun_distance >> sc.suns.sun_distance
        lc.front_value_range.front_min >> sc.value_ranges.front_min
        lc.front_value_range.front_max >> sc.value_ranges.front_max
        lc.back_value_range.back_min >> sc.value_ranges.back_min
        lc.back_value_range.back_max >> sc.value_ranges.back_max
        lc.atmospheric_perspective.enable >> sc.atmospheric_perspective.enable
        lc.atmospheric_perspective.half_distance >> sc.atmospheric_perspective.half_distance
        lc.atmospheric_perspective.color >> sc.atmospheric_perspective.color

        light_sun_pair = SunPair({'usage': 'light'}, light_direction_trans.r, make_objects=True)
        light_sun_pair.sun_position >> sc.suns.light_sun_position
        light_sun_pair.antisun_position >> sc.suns.light_antisun_position
        light_sun_pair.direction_inverse_matrix >> sc.suns.light_direction_inverse_matrix
        light_sun_pair.surface_point_z >> sc.suns.light_surface_point_z

        camera_rotation_calculator = self.utility('decomposeMatrix', 'camera_rotation_calculator')
        sc.camera.world_matrix >> camera_rotation_calculator.inputMatrix
        camera_sun_pair = SunPair({'usage': 'camera'}, camera_rotation_calculator.outputRotate)
        camera_sun_pair.sun_position >> sc.suns.camera_sun_position
        camera_sun_pair.antisun_position >> sc.suns.camera_antisun_position
        camera_sun_pair.direction_inverse_matrix >> sc.suns.camera_direction_inverse_matrix
        camera_sun_pair.surface_point_z >> sc.suns.camera_surface_point_z
