import sys, importlib
sys.path.append('/Users/calder/Documents/Animation/Shading/shading/fantasy/code/internals/reanimator')
import gradient
importlib.reload(gradient)
from gradient import gradientDescent
from pymel.core import *
from itertools import islice

# from random import random

def loss_at_time(t):
	old_cyl = SCENE.pCylinder1
	new_cyl = SCENE.pCylinder2
	attributes = [PyNode(f'joint{n}').attr(f'r{c}') for n in range(5, 9) for c in 'xyz']

	def loss_function(values):
		currentTime(t)
		for attribute, value in zip(attributes, values):
			attribute.set(value)
		dist = 0
		for old_vtx, new_vtx in islice(zip(old_cyl.vtx, new_cyl.vtx), None, None, 3):
			old_position = old_vtx.getPosition(space='object')
			new_position = new_vtx.getPosition(space='object')
			dist += sum((old - new) ** 2 for old, new in zip(old_position, new_position))
		return dist

	return loss_function

loss_function = loss_at_time(23)
values, loss = gradientDescent(loss_function, [0] * 12, startStep=20, maxIterations=1000)