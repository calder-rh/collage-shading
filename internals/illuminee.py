from pymel.core import *
from internals.network import Network
from internals.global_groups import lighting_sets
from internals.global_controls import gcn
from internals.mesh_extrema import MeasuredGradient
from internals.luminance import luminance_node
from internals.shadow_influences import shadow_distance_node
from internals.invisible import set_visibility_in_render


class Illuminee(Network):
    relevant_context = ['obj']

    def __init__(self, context, obj):
        obj_type = obj.type()
        if obj_type == 'transform':
            transform_node = obj
        elif obj_type == 'mesh':
            transform_node = obj.getTransform()
        else:
            raise Exception('Invalid illuminee input. Must be a mesh or transform node.')

        shape = transform_node.getShape()
        if shape:
            parents = listRelatives(obj, p=True)
            kwargs = {}
            if parents:
                kwargs['p'] = parents[0]
            self.control_node = group(obj, n=obj.name() + '_illuminee', **kwargs)
            parent(obj, self.control_node)
        else:
            self.control_node = transform_node

        is_new = not(self.control_node.hasAttr('used_as_illuminee'))
        if is_new:
            # Add this to the set of all illuminee nodes
            sets(lighting_sets.mesh_groups, add=self.control_node)

            # Add user customizable attributes
            addAttr(self.control_node, ln='gradient_weight', min=0, smx=1, dv=1)
            addAttr(self.control_node, ln='lights_weight', min=0, smx=1, dv=1)
            addAttr(self.control_node, ln='shadow_influences_weight', min=0, smx=1, dv=1)
            addAttr(self.control_node, ln='adjustment', min=-1, max=1, dv=0)

            addAttr(self.control_node, ln='front_value_range', at='compound', nc=2)
            addAttr(self.control_node, p='front_value_range', ln='front_min', min=0, max=1, dv=0)
            addAttr(self.control_node, p='front_value_range', ln='front_max', min=0, max=1, dv=1)

            addAttr(self.control_node, ln='back_value_range', at='compound', nc=2)
            addAttr(self.control_node, p='back_value_range', ln='back_min', min=0, max=1, dv=0.3)
            addAttr(self.control_node, p='back_value_range', ln='back_max', min=0, max=1, dv=0.7)

            # Add internal attributes
            addAttr(self.control_node, ln='internals', at='compound', nc=7)

            addAttr(self.control_node, p='internals', ln='used_as_illuminee', at='bool', dv=True)

            addAttr(self.control_node, p='internals', ln='sun_gradient')
            addAttr(self.control_node, p='internals', ln='camera_gradient')

            addAttr(self.control_node, p='internals', ln='lightness')

            self.added_lights = self.make(sets, 'added_lights', em=True)
            sets(lighting_sets.added_lights_sets, add=self.added_lights)
            addAttr(self.control_node, p='internals', ln='added_lights', at='message')

            self.excluded_lights = self.make(sets, 'excluded_lights', em=True)
            sets(lighting_sets.excluded_lights_sets, add=self.excluded_lights)
            addAttr(self.control_node, p='internals', ln='excluded_lights', at='message')

            addAttr(self.control_node, p='internals', ln='proxy_object', at='message')

            self.added_lights.message >> self.control_node.internals.added_lights
            self.excluded_lights.message >> self.control_node.internals.excluded_lights

            # Connect these attributes to the global attributes
            self.connect_to_global()

            # Multiply the weights and add them to create the raw lightness
            weighted_sun_gradient = self.multiply(self.control_node.gradient_weight, self.control_node.sun_gradient, 'weighted_sun_gradient')
            weighted_lights = self.multiply(self.control_node.lights_weight, luminance_node.luminance, 'weighted_lights')
            weighted_shadow_influences = self.multiply(self.control_node.shadow_influences_weight, shadow_distance_node.shadow_distance, 'weighted_shadow_influences')
            weighted_sum_1 = self.add(weighted_sun_gradient, weighted_lights, 'weighted_sum_1')
            raw_lightness = self.add(weighted_sum_1, weighted_shadow_influences, 'raw_lightness')

            # Correct the raw lightness for front/back dimension
            front_lightness = self.utility('remapValue', 'front_lightness')
            raw_lightness >> front_lightness.inputValue
            self.control_node.front_value_range.front_min >> front_lightness.outputMin
            self.control_node.front_value_range.front_max >> front_lightness.outputMax
            back_lightness = self.utility('remapValue', 'back_lightness')
            raw_lightness >> back_lightness.inputValue
            self.control_node.back_value_range.back_min >> back_lightness.outputMin
            self.control_node.back_value_range.back_max >> back_lightness.outputMax
            corrected_lightness = self.utility('remapValue', 'corrected_lightness')
            self.control_node.internals.camera_gradient >> corrected_lightness.inputValue
            back_lightness.outValue >> corrected_lightness.outputMin
            front_lightness.outValue >> corrected_lightness.outputMax

            corrected_lightness.outValue >> self.control_node.internals.lightness

            self.load_meshes()
            self.link_lights()
        else:
            self.added_lights = listConnections(self.control_node.internals.added_lights, s=True, d=False)[0]
            self.excluded_lights = listConnections(self.control_node.internals.excluded_lights, s=True, d=False)[0]
        
    def connect_to_global(self):
        gcn.gradients_weight >> self.control_node.gradient_weight
        gcn.lights_weight >> self.control_node.lights_weight
        gcn.shadow_influences_weight >> self.control_node.shadow_influences_weight
        gcn.adjustment >> self.control_node.adjustment
        gcn.front_min >> self.control_node.front_value_range.front_min
        gcn.front_max >> self.control_node.front_value_range.front_max
        gcn.back_min >> self.control_node.back_value_range.back_min
        gcn.back_max >> self.control_node.back_value_range.back_max
        
    def load_meshes(self):
        meshes = listRelatives(self.control_node, ad=True, type='mesh')

        proxy = self.get_proxy()
        if proxy:
            gradient_meshes = [proxy]
        else:
            gradient_meshes = meshes
        light_gradient = MeasuredGradient(self.context | {'sun_pair': 'light'}, gradient_meshes, gcn.light_sun_position, gcn.light_antisun_position, gcn.light_direction_inverse_matrix, gcn.light_surface_point_z)
        light_gradient.gradient_value >> self.control_node.internals.sun_gradient
        camera_gradient = MeasuredGradient(self.context | {'sun_pair': 'camera'}, gradient_meshes, gcn.camera_sun_position, gcn.camera_antisun_position, gcn.camera_direction_inverse_matrix, gcn.camera_surface_point_z)
        camera_gradient.gradient_value >> self.control_node.internals.camera_gradient

        for mesh in meshes:
            lightness_list = listConnections(mesh.lightness, d=False, s=True, type='floatMath')
            if not lightness_list:
                continue
            lightness = lightness_list[0]
            
            self.control_node.internals.lightness >> lightness.floatA
    
    def unload_meshes(self):
        for attribute in listConnections(self.control_node.internals.lightness, s=False, d=True, p=True):
            gcn.default_lightness >> attribute
    
    def reload_meshes(self):
        self.unload_meshes()
        self.reload_meshes()
        
    def get_proxy(self):
        connections = listConnections(self.control_node.internals.proxy_object, d=False, sh=True)
        if connections:
            return connections[0]
        else:
            return None
    
    def add_proxy(self, mesh):
        mesh.message >> self.control_node.internals.proxy_object
        set_visibility_in_render(mesh, False)
        self.reload_meshes()

    def remove_proxy(self):
        proxy = self.get_proxy()
        if not proxy:
            return
        set_visibility_in_render(proxy, True)
        self.control_node.internals.proxy_object.disconnect()
        self.reload_meshes()
    
    def add_light(self, light):
        sets(self.added_lights, add=light)
        sets(self.excluded_lights, remove=light)
    
    def exclude_light(self, light):
        sets(self.excluded_lights, add=light)
        sets(self.added_lights, remove=light)
    
    def link_lights(self):
        default_lights = set(sets(lighting_sets.default_lights, q=1))
        added_lights = set(sets(self.added_lights, q=1))
        excluded_lights = set(sets(self.excluded_lights, q=1))
        lights_to_link = (default_lights | added_lights) - excluded_lights
        
        for light in ls(type='light'):
            lightlink(object=self.control_node, light=light, b=True)
            
        lightlink(object=self.control_node, light=lights_to_link)

    def unmake(self):
        ...