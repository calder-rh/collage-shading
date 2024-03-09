from pymel.core import *
import time, datetime, threading


def set_visibility_in_render(shape, value):
    shape.primaryVisibility.set(value)
    shape.castsShadows.set(value)
    shape.aiVisibleInDiffuseReflection.set(value)
    shape.aiVisibleInSpecularReflection.set(value)
    shape.aiVisibleInDiffuseTransmission.set(value)
    shape.aiVisibleInSpecularTransmission.set(value)
    shape.aiVisibleInVolume.set(value)
    shape.aiSelfShadows.set(value)


def connect_texture_placement(placement, texture):
    placement.outUV >> texture.uvCoord
    placement.outUvFilterSize >> texture.uvFilterSize
    placement.vertexCameraOne >> texture.vertexCameraOne
    placement.vertexUvOne >> texture.vertexUvOne
    placement.vertexUvThree >> texture.vertexUvThree
    placement.vertexUvTwo >> texture.vertexUvTwo
    placement.coverage >> texture.coverage
    placement.mirrorU >> texture.mirrorU
    placement.mirrorV >> texture.mirrorV
    placement.noiseUV >> texture.noiseUV
    placement.offset >> texture.offset
    placement.repeatUV >> texture.repeatUV
    placement.rotateFrame >> texture.rotateFrame
    placement.rotateUV >> texture.rotateUV
    placement.stagger >> texture.stagger
    placement.translateFrame >> texture.translateFrame
    placement.wrapU >> texture.wrapU
    placement.wrapV >> texture.wrapV


def add_attr(obj, delete=False, **kwargs):
    attr_name = kwargs['ln']
    attr_exists = hasAttr(obj, attr_name, checkShape=False)
    if attr_exists and delete:
        deleteAttr(obj.attr(attr_name))
    if (not attr_exists) or delete:
        addAttr(obj, **kwargs)


def do_later(target, wait=0.1, wait_until=None):
    def wait_then_run():
        if wait_until:
            start_time = datetime.datetime.now()
            while (not wait_until()) and (datetime.datetime.now() < start_time + datetime.timedelta(seconds=wait)):
                continue
        else:
            time.sleep(wait)
        target()
    thread = threading.Thread(target=wait_then_run)
    thread.start()
