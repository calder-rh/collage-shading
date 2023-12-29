def make_invisible_in_render(shape):
    shape.primaryVisibility.set(0)
    shape.castsShadows.set(0)
    shape.aiVisibleInDiffuseReflection.set(0)
    shape.aiVisibleInSpecularReflection.set(0)
    shape.aiVisibleInDiffuseTransmission.set(0)
    shape.aiVisibleInSpecularTransmission.set(0)
    shape.aiVisibleInVolume.set(0)
    shape.aiSelfShadows.set(0)
