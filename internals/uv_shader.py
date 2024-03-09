from pymel.core import *
from internals.network import Network

from internals.global_controls import gcn
from internals.utilities import connect_texture_placement
from internals.palettes import get_palette


class UVShader(Network):
    relevant_context = ['mesh']
    delete = ['mesh']

    def __init__(self, context, obj, palette_path):
        if obj.type() == 'transform':
            obj_shape = obj.getShape()
        else:
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

        if not obj_shape.hasAttr('lightness'):
            addAttr(obj_shape, ln='lightness')
            gcn.default_lightness >> obj_shape.lightness
        
        palette = get_palette(palette_path)
        palette.make(1, (0, 0))

        shade_ramp = self.utility('aiRampRgb', 'shade_ramp')
        shade_ramp.attr('type').set(0)
        obj_shape.lightness >> shade_ramp.input

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
        
        shader = self.shader('surfaceShader', 'uv_shader')
        shade_ramp.outColor >> shader.outColor

        sg = self.utility('shadingEngine', 'uv_shader_SG')
        shader.outColor >> sg.surfaceShader

        sets(sg, e=True, fe=obj)
        obj_shape.aiVisibleInDiffuseReflection.set(False)
        obj_shape.aiSelfShadows.set(False)
