from pymel.core import *
from internals.network import Network
from internals.global_groups import lighting_sets
from internals.global_controls import gcn
from internals.measured_gradient import MeasuredGradient
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
            sets(lighting_sets.illuminees, add=self.control_node)

            # Add user customizable attributes
            addAttr(self.control_node, ln='gradient_weight', min=0, smx=1, dv=1)
            addAttr(self.control_node, ln='lights_weight', min=0, smx=1, dv=1)
            addAttr(self.control_node, ln='shadow_influences_weight', min=0, smx=1, dv=1)
            addAttr(self.control_node, ln='adjustment', min=-1, max=1, dv=0)

            addAttr(self.control_node, ln='min_value', min=0, max=1, dv=0)
            addAttr(self.control_node, ln='max_value', min=0, max=1, dv=1)

            addAttr(self.control_node, ln='min_saturation', min=0, max=1, dv=0.5)
            addAttr(self.control_node, ln='saturation_falloff_point', min=0, max=1, dv=0.5)

            # Add internal attributes
            addAttr(self.control_node, ln='internals', at='compound', nc=6)
            addAttr(self.control_node, p='internals', ln='used_as_illuminee', at='bool', dv=True)

            # Outputs for other networks
            addAttr(self.control_node, p='internals', ln='measurement_mesh', dt='mesh')
            addAttr(self.control_node, p='internals', ln='lightness')
            addAttr(self.control_node, p='internals', ln='saturation')

            addAttr(self.control_node, ln='proxy', at='bool')

            # Light sets
            self.added_lights = self.make(sets, 'added_lights', em=True)
            sets(lighting_sets.added_lights_sets, add=self.added_lights)
            addAttr(self.control_node, p='internals', ln='added_lights', at='message')

            self.excluded_lights = self.make(sets, 'excluded_lights', em=True)
            sets(lighting_sets.excluded_lights_sets, add=self.excluded_lights)
            addAttr(self.control_node, p='internals', ln='excluded_lights', at='message')

            self.added_lights.message >> self.control_node.internals.added_lights
            self.excluded_lights.message >> self.control_node.internals.excluded_lights

            # Connect these attributes to the global attributes
            self.connect_to_global()


            # Calculate the gradients
            light_gradient = MeasuredGradient(self.context | {'sun_pair': 'light'}, self.control_node.measurement_mesh, gcn.light_sun_position, gcn.light_antisun_position, gcn.light_direction_inverse_matrix, gcn.light_surface_point_z)
            camera_gradient = MeasuredGradient(self.context | {'sun_pair': 'camera'}, self.control_node.measurement_mesh, gcn.camera_sun_position, gcn.camera_antisun_position, gcn.camera_direction_inverse_matrix, gcn.camera_surface_point_z)

            # Multiply the weights and add them to create the raw lightness
            weighted_light_gradient = self.multiply(self.control_node.gradient_weight, light_gradient.gradient_value, 'weighted_light_gradient')
            weighted_lights = self.multiply(self.control_node.lights_weight, luminance_node.luminance, 'weighted_lights')
            weighted_shadow_influences = self.multiply(self.control_node.shadow_influences_weight, shadow_distance_node.shadow_distance, 'weighted_shadow_influences')
            weighted_sum_1 = self.add(weighted_light_gradient, weighted_lights, 'weighted_sum_1')
            weighted_sum_2 = self.add(weighted_sum_1, weighted_shadow_influences, 'weighted_sum_2')
            weighted_sum_3 = self.add(weighted_sum_2, gcn.noise, 'weighted_sum_3')
            raw_lightness = self.add(weighted_sum_3, self.control_node.adjustment, 'raw_lightness')

            # Apply the min/max adjustment to this value
            corrected_lightness = self.utility('remapValue', 'corrected_lightness')
            raw_lightness >> corrected_lightness.inputValue
            self.control_node.min_value >> corrected_lightness.inputMin
            self.control_node.max_value >> corrected_lightness.inputMax
            corrected_lightness.outValue >> self.control_node.lightness

            # Calculate the saturation
            saturation = self.utility('remapValue', 'saturation')
            camera_gradient.gradient_value >> saturation.inputValue
            self.control_node.saturation_falloff_point >> saturation.inputMax
            self.control_node.min_saturation >> saturation.outputMin
            saturation.outValue >> self.control_node.saturation


            self.load_meshes()
            self.link_lights()
        else:
            self.added_lights = self.control_node.internals.added_lights.get()
            self.excluded_lights = self.control_node.internals.excluded_lights.get()
        
    def connect_to_global(self):
        gcn.gradients_weight >> self.control_node.gradient_weight
        gcn.lights_weight >> self.control_node.lights_weight
        gcn.shadow_influences_weight >> self.control_node.shadow_influences_weight

        gcn.min_value >> self.control_node.min_value
        gcn.max_value >> self.control_node.max_value
        gcn.min_saturation >> self.control_node.min_saturation
        gcn.saturation_falloff_point >> self.control_node.saturation_falloff_point
    
    def _set_measurement_mesh(self, meshes):
        unite = self.utility('polyUnite', 'unite')
        for i, mesh in enumerate(meshes):
            mesh.outMesh >> unite.inputPoly[i]
            mesh.worldMatrix[0] >> unite.inputMat[i]
        unite.output >> self.control_node.measurement_mesh
        
    def load_meshes(self):
        if self.control_node.proxy.get():
            return

        meshes = listRelatives(self.control_node, ad=True, type='mesh')
        if not meshes:
            return
        
        self._set_measurement_mesh(meshes)

        for mesh in meshes:
            if mesh.hasAttr('lightness'):
                self.control_node.internals.lightness >> mesh.lightness
            if mesh.hasAttr('saturation'):
                self.control_node.internals.saturation >> mesh.saturation
    
    def unload_meshes(self):
        for attribute in listConnections(self.control_node.internals.lightness, s=False, d=True, p=True):
            gcn.default_lightness >> attribute
        for attribute in listConnections(self.control_node.internals.saturation, s=False, d=True, p=True):
            attribute.set(1)
    
    def add_proxy(self, meshes):
        self.control_node.proxy.set(True)
        self._set_measurement_mesh(meshes)
        for mesh in meshes:
            set_visibility_in_render(mesh, False)

    def remove_proxy(self):
        self.control_node.proxy.set(False)
        unite = listConnections(self.control_node.measurement_mesh, s=True, d=False)
        if not unite:
            return
        meshes = listConnections(unite[0], s=True, d=False)
        for mesh in meshes:
            set_visibility_in_render(mesh, True)
        self.load_meshes()
    
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
