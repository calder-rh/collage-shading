from pymel.core import *
from internals.network import Network


# class ObjWorldPlacement(Network):
#     relevant_context = ['object']

#     def __init__(self, context, obj):
#         obj_matrix = obj.worldMatrix[0]

#         obj_components = self.utility('decomposeMatrix', 'obj_components')
#         obj_matrix >> obj_components.inputMatrix

#         obj_rotation = self.utility('composeMatrix', 'obj_rotation')
#         obj_components.outputRotate >> obj_rotation.inputRotate

#         move_up_1 = self.utility('composeMatrix', 'move_up_1')
#         move_up_1.inputTranslateY.set(1)
#         point_above_obj_matrix = self.utility('multMatrix', 'point_above_obj_matrix')
#         move_up_1.outputMatrix >> point_above_obj_matrix.matrixIn[0]
#         obj_rotation.outputMatrix >> point_above_obj_matrix.matrixIn[1]
#         point_above_obj_components = self.utility('decomposeMatrix', 'point_above_obj_components')
#         point_above_obj_matrix.matrixSum.connect(point_above_obj_components.inputMatrix)

#         self.center_ws = obj_components.outputTranslate
#         self.rotation_ws = point_above_obj_components.outputTranslate


# class ObjectTransformComponents(Network):
#     relevant_context = ['object']

#     def __init__(self, context, obj):
#         obj_matrix = obj.worldMatrix[0]

#         obj_components = self.utility('decomposeMatrix', 'obj_components')
#         obj_matrix >> obj_components.inputMatrix

#         obj_rotation = self.utility('composeMatrix', 'obj_rotation')
#         obj_components.outputRotate >> obj_rotation.inputRotate

        
#         self.rotation_matrix = obj_rotation.outputMatrix

#         move_up_1 = self.utility('composeMatrix', 'move_up_1')
#         move_up_1.inputTranslateY.set(1)
#         point_above_obj_matrix = self.utility('multMatrix', 'point_above_obj_matrix')
#         move_up_1.outputMatrix >> point_above_obj_matrix.matrixIn[0]
#         obj_rotation.outputMatrix >> point_above_obj_matrix.matrixIn[1]
#         point_above_obj_components = self.utility('decomposeMatrix', 'point_above_obj_components')
#         point_above_obj_matrix.matrixSum.connect(point_above_obj_components.inputMatrix)

#         self.center_ws = obj_components.outputTranslate
#         self.rotation_ws = point_above_obj_components.outputTranslate



class RigidWorldPlacement(Network):
    relevant_context = ['object', 'facet']

    def __init__(self, context, obj, center_os, orienter_os):
        obj_matrix = obj.worldMatrix[0]

        obj_center_ws_calculator = self.utility('pointMatrixMult', 'obj_center_ws')
        obj_matrix >> obj_center_ws_calculator.inMatrix
        obj_center_ws_calculator.inPoint.set((0, 0, 0))
        self.obj_center_ws = obj_center_ws_calculator.output

        facet_center_ws_calculator = self.utility('pointMatrixMult', 'facet_center_ws')
        obj_matrix >> facet_center_ws_calculator.inMatrix
        facet_center_ws_calculator.inPoint.set(center_os)
        self.facet_center_ws = facet_center_ws_calculator.output

        rotation_ws_calculator = self.utility('pointMatrixMult', 'rotation_ws')
        obj_matrix >> rotation_ws_calculator.inMatrix
        rotation_ws_calculator.inPoint.set(orienter_os)
        self.rotation_ws = rotation_ws_calculator.output
