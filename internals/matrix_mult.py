from pymel.core import *
import sys
from pathlib import Path
sys.path = [item for item in sys.path if 'shading/fantasy/code' not in item]
code_path = str(Path(workspace(q=True, rd=True)) / 'shading' / 'fantasy' / 'code')
if code_path not in sys.path:
    sys.path.append(code_path)

import importlib
from internals import network
importlib.reload(network)
from internals.network import Network


# class ManualMatrixMult(Network):
#     relevant_context = []
#     delete = True

#     def __init__(self, matrix, x, y, z):
#         row_1_calculator = self.utility('pointMatrixMult', 'row_1')
#         row_1_calculator.vectorMultiply.set(True)
#         matrix >> row_1_calculator.inMatrix
#         row_1_calculator.inPoint.set([1, 0, 0])
#         row_1 = row_1_calculator.output

#         row_2_calculator = self.utility('pointMatrixMult', 'row_2')
#         row_2_calculator.vectorMultiply.set(True)
#         matrix >> row_2_calculator.inMatrix
#         row_2_calculator.inPoint.set([0, 1, 0])
#         row_2 = row_2_calculator.output

#         row_3_calculator = self.utility('pointMatrixMult', 'row_3')
#         row_3_calculator.vectorMultiply.set(True)
#         matrix >> row_3_calculator.inMatrix
#         row_3_calculator.inPoint.set([0, 0, 1])
#         row_3 = row_3_calculator.output

#         row_4_calculator = self.utility('pointMatrixMult', 'row_4')
#         row_4_calculator.vectorMultiply.set(False)
#         matrix >> row_4_calculator.inMatrix
#         row_4_calculator.inPoint.set([0, 0, 1])
#         row_4 = row_4_calculator.output

#         out_x1 = self.multiply(row_1.outputX, x, 'out_x1')
#         out_x2 = self.multiply(row_1.outputY, y, 'out_x2')
#         out_x3 = self.multiply(row_1.outputZ, z, 'out_x3')
#         out_x12 = self.add(out_x1, out_x2, 'out_x12')
#         out_x = self.add(out_x12, out_x3, 'out_x')

#         out_y1 = self.multiply(row_2.outputX, x, 'out_y1')
#         out_y2 = self.multiply(row_2.outputY, y, 'out_y2')
#         out_y3 = self.multiply(row_2.outputZ, z, 'out_y3')
#         out_y12 = self.add(out_y1, out_y2, 'out_y12')
#         out_y = self.add(out_y12, out_y3, 'out_y')

#         out_z1 = self.multiply(row_3.outputX, x, 'out_z1')
#         out_z2 = self.multiply(row_3.outputY, y, 'out_z2')
#         out_z3 = self.multiply(row_3.outputZ, z, 'out_z3')
#         out_z12 = self.add(out_z1, out_z2, 'out_z12')
#         out_z = self.add(out_z12, out_z3, 'out_z')


class ManualMatrixMultZ(Network):
    relevant_context = []
    prefix = 'test_matrix_'
    delete = True

    def __init__(self, matrix, x, y, z):
        decomposed = self.utility('decomposeMatrix', 'decomposed')
        matrix >> decomposed.inputMatrix

        in_x = self.subtract(x, decomposed.outputTranslateX, 'in_x')
        in_y = self.subtract(y, decomposed.outputTranslateY, 'in_y')
        in_z = self.subtract(z, decomposed.outputTranslateZ, 'in_z')

        row_3_calculator = self.utility('pointMatrixMult', 'row_3')
        row_3_calculator.vectorMultiply.set(True)
        matrix >> row_3_calculator.inMatrix
        row_3_calculator.inPoint.set([0, 0, 1])
        row_3 = row_3_calculator.output

        out_z1 = self.multiply(row_3.outputX, in_x, 'out_z1')
        out_z2 = self.multiply(row_3.outputY, in_y, 'out_z2')
        out_z3 = self.multiply(row_3.outputZ, in_z, 'out_z3')
        out_z12 = self.add(out_z1, out_z2, 'out_z12')
        out_z = self.add(out_z12, out_z3, 'out_z')

        self.z = out_z



ManualMatrixMultZ(SCENE.light_end.worldMatrix[0], SCENE.samplerInfo2.pointWorldX, SCENE.samplerInfo2.pointWorldY, SCENE.samplerInfo2.pointWorldZ)