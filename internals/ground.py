from pymel.core import *
from internals.network import Network

from internals.global_controls import gcn
from internals.utilities import connect_texture_placement, do_later
from internals.palettes import get_palette


class GroundShader(Network):
    relevant_context = ['mesh']
    delete = ['mesh']

    def __init__(self, context, obj, palette_path):
        if obj.type() == 'transform':
            obj_transform = obj
            obj_shape = obj.getShape()
        else:
            obj_transform = obj.getTransform()
            obj_shape = obj
        
        connections = listConnections(obj_shape, type='shadingEngine')
        if connections:
            old_sg = connections[0]
            for dsm in old_sg.dagSetMembers:
                connection = listConnections(dsm)[0]
                if connection.getShape() == obj_shape:
                    if obj_shape.instObjGroups:
                        obj_shape.instObjGroups[0] // dsm
                        break
        
        # Add user customizable attributes
        addAttr(obj_transform, ln='luminance_weight', min=0, smx=1, dv=0.5)
        addAttr(obj_transform, ln='light_offset', smn=0, smx=1, dv=0)
        gcn.ground_luminance_weight >> obj_transform.luminance_weight
        gcn.ground_light_offset >> obj_transform.light_offset

        addAttr(obj_transform, ln='angle_remap', at='message')
        
        # Make this treated as an illuminee
        addAttr(obj_transform, ln='internals', at='compound', nc=5)
        addAttr(obj_transform, p='internals', ln='used_as_illuminee', at='bool', dv=True)
        addAttr(obj_transform, p='internals', ln='ground_illuminee', at='bool', dv=True)
        addAttr(obj_transform, p='internals', ln='lightness')
        addAttr(obj_transform, p='internals', ln='added_lights', at='message')
        addAttr(obj_transform, p='internals', ln='excluded_lights', at='message')
        
        palette = get_palette(palette_path)
        palette.make(1, (0, 0))

        shade_ramp = self.utility('aiRampRgb', 'shade_ramp')
        shade_ramp.attr('type').set(0)
        obj_transform.lightness >> shade_ramp.input

        for shade_index, (facet_image, luminance_value) in enumerate(zip(palette.facet_images, palette.luminance_values)):
            start_index = 2 * shade_index
            end_index = start_index + 1
            shade_ramp.ramp[start_index].ramp_Position.set(luminance_value[0])
            shade_ramp.ramp[end_index].ramp_Position.set(luminance_value[1])

            image_texture = self.texture('file', f'shade_{shade_index}', isColorManaged=True)
            image_texture.fileTextureName.set(facet_image.image, type='string')
            texture_placement = self.utility('place2dTexture', f'placement_{shade_index}')
            connect_texture_placement(texture_placement, image_texture)

            image_texture.outColor >> shade_ramp.ramp[start_index].ramp_Color
            image_texture.outColor >> shade_ramp.ramp[end_index].ramp_Color
    
        # Apply atmospheric perspective

        atmosphere_blender = self.utility('blendColors', 'atmosphere_blender')
        shade_ramp.outColor >> atmosphere_blender.color2
        gcn.atmospheric_perspective.color >> atmosphere_blender.color1
        gcn.ground_atmospheric_perspective >> atmosphere_blender.blender
        
        shader = self.shader('surfaceShader', 'collage_shader')
        atmosphere_blender.output >> shader.outColor

        sg = self.utility('shadingEngine', 'collage_shader_SG')
        shader.outColor >> sg.surfaceShader

        sets(sg, e=True, fe=obj)
        obj_shape.aiVisibleInDiffuseReflection.set(False)
        obj_shape.aiSelfShadows.set(False)

        # Calculate the lightness
        
        light_dot_remap = self.utility('remapValue', 'light_dot_remap')
        light_dot_remap.inputMin.set(-1)
        gcn.other_internals.light_dot >> light_dot_remap.inputValue
        light_dot_remap.message >> obj_transform.angle_remap

        weighted_luminance = self.multiply(gcn.luminance, obj_transform.luminance_weight, 'weighted_luminance')
        lightness = self.add(light_dot_remap.outValue, weighted_luminance, 'lightness')
        lightness >> obj_transform.lightness
