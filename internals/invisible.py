def set_visibility_in_render(shape, value):
    shape.primaryVisibility.set(value)
    shape.castsShadows.set(value)
    shape.aiVisibleInDiffuseReflection.set(value)
    shape.aiVisibleInSpecularReflection.set(value)
    shape.aiVisibleInDiffuseTransmission.set(value)
    shape.aiVisibleInSpecularTransmission.set(value)
    shape.aiVisibleInVolume.set(value)
    shape.aiSelfShadows.set(value)
