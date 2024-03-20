from pymel.core import *
from internals.network import Network
from internals.global_controls import gcn, lighting_sets
from internals.utilities import add_attr, do_later


class Illuminee(Network):
    relevant_context = ['obj']
    delete = False

    def __init__(self, context, obj):
        obj_type = obj.type()
        if obj_type == 'transform':
            transform_node = obj
        elif obj_type == 'mesh':
            transform_node = obj.getTransform()
        else:
            raise Exception('Invalid illuminee input. Must be a mesh or transform node.')
        
        self.control_node = transform_node

        # Remove any illuminees that are contained in this group, since they are getting merged into this illuminee
        for transform in listRelatives(self.control_node, ad=True, type='transform'):
            if transform.hasAttr('used_as_illuminee') and transform.used_as_illuminee.get():
                transform.used_as_illuminee.set(False)
                sets(lighting_sets.illuminees, remove=transform)
                sets(lighting_sets.ground_meshes, remove=transform)
        
        # if not self.control_node.getShape():
        #     self.control_node.centerPivots()
        #     self.control_node.centerPivots()

        is_new = not(self.control_node.hasAttr('used_as_illuminee'))
        if is_new:
            # Add this to the set of all illuminee nodes
            sets(lighting_sets.illuminees, add=self.control_node)

            # Add user customizable attributes
            add_attr(self.control_node, ln='lightness_offset', smn=-1, smx=1, dv=0)
            add_attr(self.control_node, ln='contrast', min=0, max=1, dv=0)

            # Add internal attributes
            add_attr(self.control_node, ln='internals', at='compound', nc=6)
    
            add_attr(self.control_node, p='internals', ln='used_as_illuminee', at='bool', dv=True)
            addAttr(self.control_node, p='internals', ln='ground_illuminee', at='bool', dv=False)

            # Outputs for other networks
            add_attr(self.control_node, p='internals', ln='lightness')
            add_attr(self.control_node, p='internals', ln='atmosphere_blend')

            add_attr(self.control_node, p='internals', ln='added_lights', at='message')
            add_attr(self.control_node, p='internals', ln='excluded_lights', at='message')

            # Light sets
            self.added_lights = self.make(sets, 'added_lights', em=True)
            sets(lighting_sets.added_lights_sets, add=self.added_lights)
        
            self.excluded_lights = self.make(sets, 'excluded_lights', em=True)
            sets(lighting_sets.excluded_lights_sets, add=self.excluded_lights)

            self.added_lights.message >> self.control_node.added_lights
            self.excluded_lights.message >> self.control_node.excluded_lights

            # Connect these attributes to the global attributes
            self.connect_to_global()

            # Calculate the lightness
            base_lightness = self.add(gcn.default_lightness, 0, 'base_lightness', return_node=True)
            weighted_luminance = self.multiply(gcn.luminance, 0, 'weighted_luminance', return_node=True)
            do_later(lambda: self.control_node.lightness_offset >> base_lightness.floatB, wait=0.1)
            do_later(lambda: self.control_node.contrast >> weighted_luminance.floatB, wait=0.1)
            lightness = self.add(base_lightness.outFloat, weighted_luminance.outFloat, 'lightness')
            lightness >> self.control_node.lightness
        
            # Calculate the atmosphere blend (0 = fully object, 1 = fully atmosphere)
            illuminee_decomposer = self.utility('decomposeMatrix', 'illuminee_decomposer')
            self.control_node.worldMatrix[0] >> illuminee_decomposer.inputMatrix
            distance = self.utility('distanceBetween', 'distance')
            gcn.camera_position >> distance.point1
            illuminee_decomposer.outputTranslate >> distance.point2
            offset_distance = self.subtract(distance.distance, gcn.min_distance, 'offset_distance')
            num_half_distances = self.divide(offset_distance, gcn.half_distance, 'num_half_distances')
            original_color_remaining = self.power(0.9, num_half_distances, 'original_color_remaining')
            atmosphere_color_amount = self.subtract(1, original_color_remaining, 'atmosphere_color_amount')
            atmospheric_perspective_amount = self.multiply(atmosphere_color_amount, gcn.enable, 'atmospheric_perspective_amount')
            atmospheric_perspective_amount >> self.control_node.internals.atmosphere_blend

            self.load_meshes()
            self.link_lights()
            
        else:
            self.control_node.internals.used_as_illuminee.set(True)
            self.added_lights = self.control_node.added_lights.get()
            self.excluded_lights = self.control_node.excluded_lights.get()
        
    def connect_to_global(self):
        if self.control_node.ground_illuminee.get():
            gcn.ground_luminance_weight >> self.control_node.luminance_weight
            gcn.ground_light_offset >> self.control_node.light_offset
        else:
            gcn.default_contrast >> self.control_node.contrast

    def load_meshes(self):
        meshes = listRelatives(self.control_node, ad=True, type='mesh')
        if not meshes:
            return

        for mesh in meshes:
            if not mesh.hasAttr('lightness', checkShape=False):
                addAttr(mesh, ln='lightness')
            self.control_node.lightness >> mesh.lightness
            if not mesh.hasAttr('atmosphere_blend', checkShape=False):
                addAttr(mesh, ln='atmosphere_blend')
            self.control_node.atmosphere_blend >> mesh.atmosphere_blend
    
    def unload_meshes(self):
        for attribute in listConnections(self.control_node.lightness, s=False, d=True, p=True):
            gcn.default_lightness >> attribute
        for attribute in listConnections(self.control_node.atmosphere_blend, s=False, d=True, p=True):
            attribute.set(0)
    
    def add_light(self, light):
        sets(self.added_lights, add=light)
        sets(self.excluded_lights, remove=light)
    
    def exclude_light(self, light):
        sets(self.excluded_lights, add=light)
        sets(self.added_lights, remove=light)

    def reset_light(self, light):
        sets(self.excluded_lights, remove=light)
        sets(self.added_lights, remove=light)
    
    def reset_lights(self):
        sets(self.excluded_lights, clear=True)
        sets(self.added_lights, clear=True)
    
    def link_lights(self):
        default_lights = set(sets(lighting_sets.default_lights, union=ls('::default_lights', sets=True)))
        added_lights = set(sets(self.added_lights, q=1))
        excluded_lights = set(sets(self.excluded_lights, q=1))
        lights_to_link = (default_lights | added_lights) - excluded_lights

        lightlink(object=self.control_node, light=ls(type='light'), b=True)
        lightlink(object=self.control_node, light=lights_to_link)

    def unmake(self):
        ...


def make_illuminee(obj):
    return Illuminee({'obj': obj.name()}, obj)
