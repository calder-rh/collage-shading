from pymel.core import *
from internals.global_controls import lighting_sets
from internals.illuminee import make_illuminee


def reload():
    illuminees = [item for item in ls() if item.hasAttr('used_as_illuminee') and item.used_as_illuminee.get()]
    default_lights = set(sets(SCENE.default_lights, union=ls('::default_lights', sets=True)))

    for node in illuminees:
        if not node.ground_illuminee.get():
            illuminee = make_illuminee(node)
            illuminee.load_meshes()
            print(node.name())

        added_lights = set(sets(node.added_lights.get(), q=1))
        excluded_lights = set(sets(node.excluded_lights.get(), q=1))
        lights_to_link = (default_lights | added_lights) - excluded_lights

        lightlink(object=node, light=ls(type='light') + ls(type='aiSkyDomeLight'), b=True)
        lightlink(object=node, light=lights_to_link)
