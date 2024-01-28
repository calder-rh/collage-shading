from pymel.core import *
from internals.network import Network
from math import floor


class CoordinateConverter(Network):
    relevant_context = ['mesh']

    def __init__(self, _, obj):
        self.transform = obj.getTransform()
        self.shape = obj.getShape()

        uv_to_xyz_calculator = self.utility('pointOnPolyConstraint', 'uv_to_xyz_calculator')
        target = uv_to_xyz_calculator.target[0]
        mesh = self.shape.outMesh
        mesh.connect(target.targetMesh)
        self.u_in = target.targetUV.targetU
        self.v_in = target.targetUV.targetV
        self.xyz_out = uv_to_xyz_calculator.constraintTranslate

        xyz_to_uv_calculator = self.utility('closestPointOnMesh', 'xyz_to_uv_calculator')
        result = xyz_to_uv_calculator.result
        mesh.connect(xyz_to_uv_calculator.inMesh)
        self.xyz_in = xyz_to_uv_calculator.inPosition
        self.u_out = result.parameterU
        self.v_out = result.parameterV
        self.vertex_out = result.closestVertexIndex

        self.last_calculation = [0, 0, 0]

    def pixel_to_uv(self, px, py, resolution):
        u = (px + 0.5) / resolution
        v = ((resolution - py - 1) + 0.5) / resolution
        return u, v

    def uv_to_pixel(self, u, v, resolution):
        px = floor(u * (resolution - 1) + 0.5)
        py = floor((1 - v) * (resolution - 1) + 0.5)
        return px, py

    def uv_to_xyz(self, u, v):
        self.u_in.set(u)
        self.v_in.set(v)
        result = list(self.xyz_out.get())
        if result == self.last_calculation:
            return [None] * 3
        else:
            self.last_calculation = result
            return result

    def xyz_to_uv(self, xyz):
        self.xyz_in.set(xyz)
        return self.u_out.get(), self.v_out.get()
    
    def xyz_to_vertex(self, xyz):
        self.xyz_in.set(xyz)
        return self.shape.vtx[self.vertex_out.get()]

    def pixel_to_xyz(self, px, py, resolution):
        return self.uv_to_xyz(*self.pixel_to_uv(px, py, resolution))
    
    def xyz_to_pixel(self, xyz, resolution):
        return self.uv_to_pixel(*self.xyz_to_uv(xyz), resolution)
