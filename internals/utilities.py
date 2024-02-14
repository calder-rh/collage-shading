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
