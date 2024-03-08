from pymel.core import *
from internals.network import Network
from internals.global_controls import gcn
# from internals.utilities import do_later


class AtmosphericPerspective(Network):
    relevant_context = ['mesh']
    
    def __init__(self, _, object_color):
        object_hsv = self.utility('rgbToHsv', 'object_hsv')
        object_color >> object_hsv.inRgb
        object_luminance = self.utility('luminance', 'object_luminance')
        object_color >> object_luminance.value

        target_color = self.utility('blendColors', 'target_blend')
        gcn.color >> target_color.color2
        target_color.color1.set((1, 1, 1))
        object_luminance.outValue >> target_color.blender

        target_hsv = self.utility('rgbToHsv', 'target_hsv')
        target_color.output >> target_hsv.inRgb

        atmosphere_blend = self.utility('blendColors', 'atmosphere_blend')
        object_color >> atmosphere_blend.color2
        target_color.output >> atmosphere_blend.color1
        gcn.atmospheric_perspective_amount >> atmosphere_blend.blender

        blend_hsv = self.utility('rgbToHsv', 'blend_hsv')
        atmosphere_blend.output >> blend_hsv.inRgb

        blend_luminance = self.utility('luminance', 'blend_luminance')
        atmosphere_blend.output >> blend_luminance.value

        saturation_lerp = self.utility('remapValue', 'saturation_lerp')
        gcn.atmospheric_perspective_amount >> saturation_lerp.inputValue
        object_hsv.outHsvS >> saturation_lerp.outputMin
        target_hsv.outHsvS >> saturation_lerp.outputMax

        blend_s_over_lerp_s = self.divide(blend_hsv.outHsvS, saturation_lerp.outValue, 'blend_s_over_lerp_s')
        flip_1 = self.subtract(1, blend_s_over_lerp_s, 'flip_1')
        power = self.power(flip_1, gcn.enhance_saturation, 'power')
        flip_2 = self.subtract(1, power, 'flip_2')
        adjusted_saturation = self.multiply(flip_2, saturation_lerp.outValue, 'adjusted_saturation')
        
        color_with_max_value = self.utility('hsvToRgb', 'color_with_max_value')
        blend_hsv.outHsvH >> color_with_max_value.inHsvR
        adjusted_saturation >> color_with_max_value.inHsvG
        color_with_max_value.inHsvB.set(1)
    
        cwmv_luminance = self.utility('luminance', 'cwmv_luminance')
        color_with_max_value.outRgb >> cwmv_luminance.value
        luminance_ratio = self.divide(blend_luminance.outValue, cwmv_luminance.outValue, 'luminance_ratio')
        
        color_with_target_luminance = self.utility('aiMultiply', 'color_with_target_luminance')
        color_with_max_value.outRgb >> color_with_target_luminance.input1
        for primary in 'RGB':
            luminance_ratio >> color_with_target_luminance.attr('input2' + primary)
        
        self.color = color_with_target_luminance.outColor
