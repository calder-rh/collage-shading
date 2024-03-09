from pymel.core import *

def run():
    for mesh in ls(sl=True, dag=True, shapes=True):
        mesh.aiTraceSets.set('')
        mesh.aiVisibleInDiffuseReflection.set(False)
