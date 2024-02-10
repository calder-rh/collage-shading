from pymel.core import *
from internals.illuminee import Illuminee


def reload():
    illuminees = set(sets(SCENE.illuminees, union=ls('::illuminees', sets=True)))
    default_lights = set(sets(SCENE.default_lights, union=ls('::default_lights', sets=True)))

    for illuminee_node in illuminees:
        illuminee = Illuminee({illuminee_node.name()}, group)
        illuminee.load_meshes()

        added_lights = set(sets(illuminee.added_lights, q=1))
        excluded_lights = set(sets(illuminee.excluded_lights, q=1))
        lights_to_link = (default_lights | added_lights) - excluded_lights

        lightlink(object=illuminee.control_node, light=ls(type='light'), b=True)
        lightlink(object=illuminee.control_node, light=lights_to_link)
