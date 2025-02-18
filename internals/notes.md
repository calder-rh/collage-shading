ok
what am I going to do

first I am going to adjust the palette settings so that it actually uses the filenames
s1 s2 etc

ok so what should the name of the orienters be?
cso_1

wait. better.
have a group called facet_orienters


ok now adjust this. because, duh, you can just select the orienter based on whichever one is closest to the facet.
how does that work? it needs to happen in the surface values.
give it a list of the names and world coordinates of all orienters.
so, how to identify orienters? what objects should it look through? I think there should just be a group called facet_orienters, and any transform node (that isn't a group) is counted. that's easier than requiring a certain name.

ok so something is up with the uv pin.
I will do this manually. yayyyyy
I've selected a vertex. need to get the 

oh wait.
i'm dumb

use the cyan pixel within a facet to indicate where on the surface the pin should be attached. lol.


TODO
turn off self shadows on all objects with collage shaders
remove camera world matrix from SC
attach SC to the remapped facing ratio
add an extra point or two in the graph of the RFR

ok what I will do now:
I realized it doesn't look good to have that shiny part. the highlight. I'm going to remove that.

duh. I realize I need to remap luminance. that's not hard.

thought:
if the default shader path is to a folder of shaders, then just make that the prefix.

what is the easiest way to do this?
in the map data file, store whatever palette info is specified in the white region, if any
when choosing a facet for a palette:

ok hmm
better idea, maybe…
you'll never have cyan or yellow pixels outside. use cyan. why not


out_data['global palette'] = 








Ok.
Time to figure out lighting!!!!
yay!!

Each mesh is defined to be a part of a lighting object (LO)
each LO is given a lighting control, which determines the center and size of the gradient
(lighting controls are put on a separate layer, I think)
There is one object that determines the overall direction of the light and controls all the lighting controls
(Should it be possible to have multiple lights if some objects need different directions? I think so…)
The shading controller determines the range of lightness that is allowed, varying it from near to far to create an effect of atmospheric perspective

how to determine LOs? I think you just select objects (or select a group) and press a button
so:
a button to make a light
a button to make a LO
and a button to apply a light to an LO
    if you don’t have an LO selected, it will apply to all remaining LOs
    if you select two lights, it will replace everything lit by one light with the second light

I think I will go with the linear gradient thing, especially since I realize that (duh) I can use an aiDot node





all right
so
what do I do now?

how much does this replace of the shading controller?
eh
I think I’ll just have a lighting controller in addition to a shading controller
maybe there should be two pairs of suns?
one for the scene and one for the camera.
the camera suns are affected by the shading controller
and you can determine how much each affects the lighting

okay so right now there are no things you actually need to edit manually with the shading controller. since luminance factor isn't going to be a thing.

lighting controller has
sun direction (by rotating the handle)
sun distance
min light (default 0)
max light (default 1)
weight between scene sun vs camera distance
atmospheric perspective:
    min distance
    max distance
    max adjustment

how to sort these?


the shading comes from
    scene suns
    camera suns
    proximity to characters
should objects also cast directional shadows? nah, figure this out later.

with references, it worked to have several shading controllers
but here I think it would be confusing to have multiple suns.
Maybe the shading controller is still used to pass the sun values onto all the objects. I think that makes sense.
so
there is one lighting controller. you can press a button that generates a lighting controller attached to the top-level shading controller, and deletes the previous lighting controller if it exists
sounds good


hmm ok so uh
how should the sun pairs be grouped?

what extra object does this make?
shading controllers
one lighting controller
a sun pair

ok so it should be something like

shading_controls
    lighting_controller
    internals_dont_touch
        shading_controller
            ...referenced shading controllers
        world_suns
            sun
            antisun

what are the outputs? the position of the two suns.


Ok. So. Now how do I *use* the measured gradients…

This is now where it starts to interface with a shader.
So I guess I’ll attach shaders to these objects

all right so each shader now has a luminance node. how to access them? ok that's easy

so now what to do if you select a group of objects where some/all of them already are part of lighting groups?
each of those lighting groups get redone to include just the remaining object(s).
ugh.

how to tell what lighting group an object is part of?
I guess I can build some infrastructure to make that easier, like a shading group
or there can just be a string attribute
how to keep track of all the group names though? I guess it can just be the timestamp at which the group was created
well. okay. I will actually create an empty group representing it


ok so for later what I'll do is:
when you want to create a new LG from selected objects
it goes through each of those objects and sees whether it is connected to an LG already
if it is:
    disconnect from that LG
    add that LG to a list of edited LGs
then go through the list of edited LGs
    if any of them is empty, destroy the network
    for the other ones, regenerate the network

also I need to separate the code that makes LGs from the code that makes measured gradients. LG should be the input to the MG — the context should be lighting_group and sun_pair

I also want to be able to use a proxy object for the group, that determines the gradient instead of the object itself



ok
so at the moment, the system of shading controllers is responsible for getting global information (about camera) to all the individual collage shaded objects.
but it seems like now I’m having some kind of system for lighting where there’s just one level. how does that work?

the illuminee lighting controller is stored in each file for each illuminee. it has the instructions.


so why does the shading controller system have to be different? right now I think it's just a relic of the old way of doing things, perhaps...
right now:
the shading controller is what is responsible for passing the camera information to each fantasy shaded object

so each file can have a global lighting controller.
it's just only the top one that's connected to anything.
they'll all get unique names because of namespaces and referencing

so. no more shading controller
I think I'll take the path of renaming it and not refactoring so I can see where I need to make changes.


what happens if you split an illuminee?
each mesh has a mesh extrema calculator


ok so I think the GLC becomes responsible for passing on camera info. yay



now what
illuminee lighting controller

so I know I want to have a set to control membership in an illuminee

ok so at the moment the illuminee is an entirely different object stored in a different place
but I think that any group of objects making up an illuminee will be a group anyway. so I’ll just do that. much easier.

so to make an illuminee you’ll select a group. (or select some objects, which will make a group)
that will be the input to the illuminee object

it should be possible to reload an illuminee. just look at the objects in it.
ok so I still want to have a set of all illuminees. just don’t need to have sets of the individual objects

what about single-object illuminees? do they get a new group? yeah I think so

ok so how do these sets work
so there's a global set
one for the transform groups containing the meshes
don't need partition

hmm how does reloading work? it needs to delete everything... how does it know what to delete?
does it need a set?
I don't think so. I'll try to do without it.

so what happens when you assign a shader? Its input is not connected to anything yet.
when I create a shader, I’ll attach the luminance input to the mesh it's shading
so when you say you want to make an illuminee out of a group:
    iterate through all of the transform nodes that are its children
    for each of these, get the shape node
    use that shape node to calculate the near/far
    and from the shape node, see the floatMath it's connected to and connect the luminance to that. ok cool


also I wonder:
maybe all you have to do when creating an illuminee is
    create the initial nodes and attributes
    reload
so some of this logic should go in the reload (or I'll just call it load)


ok so how do proxies work?
should a proxy be allowed to be in a different group?
should it be *required* to be in a different group?
I think the latter is maybe the easiest...

so then if you have a group of several objects with a proxy, it's like
group
    illuminee
        mesh
        mesh
        mesh
    proxy


what if there's an illuminee group that has transform nodes under it which themselves contain meshes?
illuminee
    transform
        mesh

I think that should count

ok so what is each mesh used for?
to calculate the gradient
& to get the shader to input

ok so in a moment I'll work on light linking

how does light linking work? why do I need to store extra things?
why can't I just do light linking?
because with regular light linking, when you make a light, it will automatically connect to everything

ok how to make a shadow influence?
I think this doesn't even have to be a class. just select an 


all right I want to deal with this import business.
first I want to make a simple test case

ok I've gotten most of the way there but I'll finish it later
I realized that ideally I need to be able to look at the imported modules and see what *they* import. might have to add it to the sys_modules argument as well...

ok so what am I doing now


… how do references work?
you just have to bring everything in the sets of the referenced file into the set of the main file





all right.
so now I want to try this grass thing.

my question is: how much of the calculations should be done by nodes, and how much should be done by code?

ok well first I'm going to adjust this to make the scale constant. done.

ok. so.
what do I need to calculate?

I need to take the camera position and rotation, draw lines based on that, and find where those lines intersect the plane. I think that might be easiest done through code
at least, I should probably learn how to multiply matrices in Python since that's generally useful

but before I continue I should figure out what the math is, and then figure out where to implement the math.


ok so
I will want to use a screen placement network so I don't have to do the calculation manually
or maybe that isn't such a problem?

again. figure out the math beforehand.
sure ok I'll try just doing this by "hand"

I don't think I need a special class —
instead I just need a function that creates an AnimCurve.
well ok I guess that needs to have a name and be part of a network. whatever

ok how exactly does this work?
well. I want one function that takes a screen y coordinate and outputs a uv coordinate

oh right I can't do matrix multiplication easily because I can't import numpy within maya :|
…it's not hard to write a function to do it.

all right so I can get the world xyz coordinates given a screen interp y. what next?
This is used for two things: animating the boundaries between regions, and animating the positions of the textures.

I do need to make the network that takes the shaderInfo xyz position and determines where it is in the y_interp
like the inverse of this.
I think I'll feed that into a rgb ramp that goes between the images

ok how to calculate this...
make a composeMatrix that just has the camera tx, tz, and ry. invert the output. get the relevant components and multiply with world x and z of samplerInfo. that gives the flat distance value
convert the flat distance to a screen space y, between -0.5 and 0.5
put that y into a remapValue where the input min is -0.5 and input max is either 0.5 or horizon, whichever is smaller. output between 0 and 1
take the output of that and put it into the ramp.
ok cool. will do that after visiting.

I think I'll just try doing the actual animation


ok. reconsidering.

so as the camera animates, we maintain variables for the camera x, z, and theta (projected y rotation)
and a list of the d values (distance from camera along xz plane) for each band

originally I thought it would be necessary for bands to come and go, so we can ensure that no matter how far the camera moves, there are always enough in frame
But I don't think the camera is going to move enough to make this necessary. If the camera is going to make a big move, the user can increase the number of bands.

I think it might make sense to have a different controller for the ground, since that lets you set the ground y visually
(or maybe it's parented to the global controls, not sure)
but wherever the ground controls are,
you use them to set the *initial* placement of the bands: what is their spacing, how many are there, and what portion of them are behind the camera?
and maybe also, how large should the fade be relative to the bands?


so we have this list of band distances, and we know how they & the camera move over time
for each frame, we also want to get the uv coordinates associated the point in the center of the band
given the point d away from the camera in direction theta, find the closest point on the mesh to that point, and get the uv coordinates of that point. find the xyz coordiantes of that uv. then find the xyz coordinates of where it's going to be in one frame.
convert both of those xyzs to screen space and take the difference. that gives the difference in placement values
the rotation of the texture is always 0
the scale of the texture is determined by the (inverse square root of the) distance from the band center to the camera



ok so what nodes actually need to be made here?
this is not a tracking projection
it's a new type of thing.
for each band, need an image:
        placement node
        file node
        projection node
all of these are used as stops on the
    rgb ramp
the input to that ramp is calculated by
    samplerInfo to get x and z
    floatMaths to dot product that with the camera theta components




^ will return to this later
I want to make the lighting controller work with namespaces before I forget
let’s geaux
there has to be a function that reloads
ok cool it can just look to see if there is a set with a given name.

to do:
    - finish the above
    - change how lightness is passed
    - change how meshes / proxies are organized
    - make it work to apply a new shader (2 might already fix that)
    - change system to do the desaturation thing
    - noise
    - make shadow influences part of global network

idea:
rather than having the proxy field be a message
have it be of type mesh, and then you can input that field to the range calculator
further idea:
see if it’s possible to use a polyUnite node to create one mesh from many. then that can also be the input to the calculator, and you don’t need the min/max nodes

I will also make the lightness field of each mesh just be an actual int rather than linking to some other node



all right so: new illuminee meshes thing
how to keep track of proxy and output?
What is simplest for the measured gradients is to have one node that is whichever mesh needs to be measured, which could either come from a proxy or a combination of several child meshes
if you have a proxy, is there any reason the node has to be connected to the meshes otherwise? no: because it’s still the parent of them.
hmm but: if there is a proxy, you have to know that it is a proxy when you reload.
ok so that can be a boolean then. if it’s checked, then don’t reload the meshes



hmm wait um
how do referenced things work?
Because I think it would work equally well to just connect this file’s global controls to the global controls of the imported file

why do you need to keep track of the mesh groups to begin with? what do you need to do with them?
you need them so you can keep track of lights I guess. well really to reload anything.
but it’s not that hard. when searching for things to reload, just look in all sets named ::set_name
cool

will do this after figuring out some of the other things


oh wait um
how do default lights work with referenced files?
well I think it probably doesn’t matter much because you’re unlikely to be importing a scene with a light to a scene with another light
but in case it matters:

ok so when resetting a light to default
if you select an illuminee, it clears the set of added & excluded lights
if you select a light, it removes it from all illuminees’ sets
if you select a light & illuminee, it removes it from that illuminee’s sets


ok I’ll try this atmospheric perspective thing…




TODO is it possible to convert to HSL and use that instead of HSV?
ok yeah so something is up with the value
e.g. going from orange to sky blue. it gets way lighter than either of the endpoints
in the middle, it should not get lighter than the blend.
actually it never should

start: 0 to 1
end: 0 to blend / 0 to atmosphere 

oh I think what I want is:
make one node that takes the object color and increases value to 1
a separate blend between that and the atmosphere color
and make that the max. (?)

ok no on that
I should find some way to use the luminance node to correct it. want to choose whatever lightness value causes the luminance to change smoothly.
how to do that though?

the luminance should fade smoothly
so find the luminance of the start, the luminance of the end, and use a remapValue to lerp between them
then take the luminance of the blend, and use that to calculate the corrected lightness to feed into the resulting color

the final lum should be
luminance of the original, scaled to 

ok try number whatever:
take the blend. directly convert that to whatever we want the luminance to be.
then use that to calculate the hue and saturation

all right, well, something with the luminance makes it feel more smooth, but also less saturated. maybe i want something in between.




ground time!
so what is the best way to make this work?
the ground gets its own illuminee, which by default has the gradient at weight 0
the ground shader has to be different than other things, since bands & facets don’t work the same

some of the things are going to be calculated by the python program, not by nodes. what does need to be nodes?
there needs to be that network that calculates the flattened version of the ground and feeds it into a closestPointOnMesh
only need one of those; can use that to query each of the points
also need the pointOnPoly constraint

need to have some node that calculates the direction of the camera as projected onto the ground
I guess that’ just the camera direction vector, with y set to 0, and then normalized
the shader is made of a ramp. the input to that ramp is the dot product of the ground camera direction with the samplerInfo xyz, subtracted from some offset value that changes as the camera moves forward/backward
each of the stops on the ramp is itself a ramp, the same as you’d have in a facet (input is light, stops are images)

I guess there are two problems that can be approached separately
one of them is dividing the surface into bands on this ramp
the other is placing the textures within the bands

do I want a Band object? I was going to have that


to keep track of the bands’ motion, just need to keep track of one value: the distance (along the ground, in the camera direction) from the camera to the band with index 0
all the other band positions are calculated based on that
so the idea is: track the camera’s motion and calculate how this changes. this gives a sequence of values, one for each frame
store the band width globally, so all the bands need to store for themselves are their indices

then to calculate the texture placement
in each frame, for each band:
use the camera position, band distance, band index, and band width to find the x, z coordinates of the center of the band.
find the uv coordinates of the point on the ground with that xz
then look at where those uv coordinates are in the next frame
this gives a pair of xyz coordinates. translate each of them to screen coordinates, and take the difference. translate each of the shades of the texture by that much.

ok so I guess the band object should store the texture ramp and a list of the textures making it up

well I don’t actually feel like doing this now, lol. I won’t.



ok so for the ground
does it need to be able to work with more than one mesh?
yes: there are the scenes that show both sides of the cliff.

oh hmm what *about* the cliff?
and the edge between them? I can’t just say: this whole mesh is the ground. because then it would shade the edge of the cliff and the top the same.
I guess I should actually load the file and look
okay yeah each landmass is one mesh. hmm…

a few options:
cut a seam around the edge and apply one shader to the top and another to the sides
    this is bad because the edge would be hard
divide it into facets and have one of them be shaded ground-ly
    this is more flexible but I *don’t* want to implement this
base it on the angle of the surface
    there are no very steep hills so this could actually work?

I will need to figure out a way to handle the case where the center of the band is not present because of the cliff
or where the whole band isn’t present because it’s too far

wtf maya
you don’t have a way to incorporate the normal direction into a shader
okay yes there is a horrible workaround. yay!

although now even though I figured that out
that doesn’t solve the problem of what to do about the cliff.
I will let that be a problem for Future Guy



ok so wait this maybe does only work on a per-mesh basis, because it relies on using the uv coordinates
remember the point is to present something in class today. it’s okay if it’s just one mesh.


so when it regenerates the ground, does it delete all the previous bands, or what?
well what is there in each band?
a ramp, a set of textures, a texture placement, and some animCurves
is that all? might be
oh also an illuminee (for the ground)


wait what am i doing
do I actually need to calculate the camera ground vector itself
or only a matrix that is pointed in its direction
it’s used for two things:
    determining the distance in the camera direction, as an input to the ramp
    finding the x/z coordinates of the center of a band
well, the latter doesn’t have to be done in Maya; that’s done in Python and can just be basic trig
but I do want the former


ok so now what
actual bands. 38 minutes before class, lol
what does this involve
so there’s the ramp
input between 0 and 1
that needs to be transformed based on the band size, band offset, and number of bands
ok do this in several steps

well first… I think I need to add these settings to the global controls
i guess most of these are for the purpose of generating things later, more as easy inputs to a program

what is input to the ramp?
that is, what is the remapValue

band offset = the distance (along the ground, in the camera direction) from the camera to the band with index 0
so
input min = offset
input max = offset + spacing * count

then just evenly space the boundaries along the ramp

ok how to add stops
well I’ll figure that out later; I’ll do a placeholder for now


ok so if I use a remap I have to do
calculate offset + spacing * count (that’s 2 nodes) and input them
if I’m just doing regular math nodes, then I’m taking (gz - offset) / (spacing * count)
ok easier


now time to animate the offset.
need to keep track of camera x/z, and camera ground vector


ok so I have all the band offset animation taken care of.
now I actually have to put in the textures.
how will this work?

so how does a GroundBand object interact with things?
in particular, who does the animation?
and who calculates the position etc

ok so I think I can reuse / repurpose TrackingProjection, to convert the screen placement values to image placement
all that is required of the screen_placement is that it have attributes for position_x, position_y, rotation, and scale.
an animated screen placement could just be a collection of four animCurves


ok cool
focal length factor = focal length / aperture

so I have the world xyz now
and want to convert it back to camera x, y
that calcuation is:

c_xyz = [camera inverse matrix] * w_xyz
s_xy = c_xy * (focal length factor) / (-c_z)


ok what are the conversions I need to make again?
screen x → uv
    done
uv → world xyz
    just use the inputs and outputs of the ground
world xyz → screen xy
    
screen xy → texture placement

ok so the scale is global scale / z depth
which is perfect because we have the z depth

ok so
how do we place the textures again?
for each uv coord,
look at the xy_ss at the previous frame and current frame, and find the difference
average those
then set the xy_ss at this frame to be whatever it was at the last frame plus that average difference

but the question is what to do at the beginning.


                l = createNode('locator')
                l.getTransform().t.set(ground_xyz)
                parent(l.getTransform(), g1)

Huh okay
So when the x or y offsets are really large, that somehow messes up the texture placement. The relationship between a change in xy_ss and a change in offset uv should be linear, but it’s not...

OK so it seems like there’s nothing wrong going on with those calculations — it’s just that placements look weird when translate frame is really large in either direction
I’m not really sure how to deal with that...




ok so for angle based shading I need to
- get the normal vector in camera space
- multiply by camera world vector to get normal vector in world space
- dot that with light direction vector

or maybe it is more efficient to
- convert light direction vector to camera space (inverse camera matrix * l.d.v.)
- get normal vector in camera space
- dot



how to better combine the different types of shades...
I think the core point is that you want to apply a float ramp to the dot product before adding it to other stuff. put that ramp into the set.
how does this apply to other illuminees? hmm…
I think I’ll have it work the same way for any illuminee
oh wait it already exists. lol.


todo:
finalize (as much as I can) the atmospheric perspective math. (maybe can add some extra controls in there...)
add an option to make a uv shader.
make a script that builds the buttons & shelf automatically (deleting what is already there)
…is that it?


ok. so. redoing this atmospheric perspective thing......
what we have now:
black → black
color → color
white → color
what I want:
black → gray
color → color
white → white
right now it’s like the paper gets colored a certain color and you drew in black on it
while I want the paper to stay white and your drawing gets more narrow in hue
how to achieve this?

actually… is this what I want? I’m just confused about what black & white should map to, and how much control you should have over that.
forget about hue change for a moment. imagine if you have a monochrome image that goes from black to sky-blue to white.
when it’s farther away it should go from… um
being realistic, it would be dark blue to light blue
but I like this idea that you’re just putting less ink on the paper in the background.
dark blue to blue to white.
do I want to make sure that anything that is the exact color of the atmosphere stays that color?
like if the atmosphere is light blue… I don’t want something that is light blue to get lighter so that darker things can match it
never mind I’ll let that happen

so how do I want to work this…
do I want to say that black becomes the atmosphere color? or gray? I don’t want to desaturate things too much.
let’s say the atmosphere color is 



front:
black → black
dark blue → dark blue
sky blue → sky blue
light blue → light blue
red → red
white → white

middle:
black → very dark blue
dark blue → mostly dark blue
sky blue → sky blue
light blue → o
red → purple
white → white

back:
black → dark blue
dark blue → medium-dark blue
sky blue → sky blue
light blue → light blue
red → blue
white → white


ok figure this out. what do I want? how to get what I want?
I know what the beginning and end are. the middle is what confuses me.

previously what I’ve done is:
use amount to blend
    object
    use object lightness to blend
        atmosphere color
        white

I want to achieve the same effect with the lightness blend on the outside. is that possible?
hmmmmmmmm maybe not… since lightness is a complicated value

why do I want to do that?
the maximum lightness is always 1. the minimum lightness has to go from 0 to whatever is the lightness of the atmosphere color.
so I can make a network that takes some color and remaps its lightness to this scale.

What color goes into that network?
it has to start as the object color.
and can end at the atmosphere color.

so naively you’d just blend from one to the other
but I’ll do my fancy saturation adjustment thing.

ok how to make the network that remaps the lightness?
um
oh wait yeah.
take the input color and calculate its lightness. Then calculate desired lightness / input lightness. and then multiply that by
no that doesn’t work. because even if the desired lightness is 1 it won’t necessarily produce white.
previously I just blended with white. how can I do this here?
um

oh hmm
ok so I think the lightness will only increase
so I have ri, gi, and bi (input) and want ro, go, bo (output)
how much do they need to be blended with white to produce the given luminance?
let’s say the blend amount is A.
so
lo = x[1-A(1-ro)] + y[1-A(1-go)] + z[1-A(1-bo)]
ok wait I think there should be a simpler way to do this

for each of the rgb components, make a remapvalue with
output min: ranges from 0 to the luminance of the atmosphere
output max: 1

ok wait why doesn’t that work
oh yeah. because I’m giving the input as the blend

what should the input be?
what if I let it be the original image
so do I just want it to be the original image but with adjusted saturation? …and hue?


💡+
💡−

set camera

make collage shader
make uv shader
make ground shader

make palette settings
make uv file

make illuminee
proxy
reconnect illuminee to global settings
reload illuminees

add light
exclude light
reset light

make influence
remove influence

load reference





set
camera

[camera]

flat [shaded]
uv [shaded]
ground [shaded]

collage
map

uv map [uvEditorShell]
palette [advancedSettings]

illum
proxy
🌎weights
reload

+light
−light
🌎light

+infl
−infl

ref

flat
shader

uv
shader

ground
shader

palette
settings

illum
inee

proxy
shape

shadow
infl +

add
shadow
infl




TODO: saturation isn’t working…
need to make more illuminee controls that let you create groups (e.g. petals, stems)
which can be linked to other groups or not
see how it looks to multiply gradient by light (maybe remapped light or something)
flower petals should look more glow-y, more translucent. not full dark on the bottom
keep some of the light influence, just to show a little bit of the shape

note: I might be able to get world normal using an aiUtility shader set to normal



ok. so what did we decide…
No gradients or shadow influences on anything
ground is influenced by light and dot
foliage is mostly constant but maybe influenced a little by light
everything in an illuminee has a constant atmospheric perspective / blend adjustment defined by the distance from the illuminee to the camera
maybe: shaders randomly choose one point along the scale as the center? actually you can adjust that yourself.

this means I don’t need suns anymore, which is nice

so how is an illuminee built?
for an object the controls are:
lightness adjustment (not linked to anything)
contrast amount
    → min and max lightness are overall ± contrast / 2

oh that’s it. nice

oh: one thing I needed to do was to make it so you can select either a palette or a map.

for ground it’s similar to before.
I wonder if I should have an illuminee base class that then defines


what are the buttons?

set camera
—
collage shader
ground shader
—
collage map
palette options
—
make illuminee
reconnect values (? maybe only applies to contrast now)
reload illuminees (yes)
—
add light
exclude light
reset light
—
setup refs
—
system check




the shading controls now just go at top level
what are they, now?

base light amount (0.5)
default contrast

atmospheric perspective:
enable
color
half distance

texture scale
camera stuff
no sun stuff



how to handle ground? is it even an illuminee? it’s fully different from the others.
I don’t think it has to be. It can just be added to the illuminees group so that it’s linked/unlinked from lights
or, better, have another global group for ground meshes. (?)

how to deal with controlling multiple ground meshes?
setting the remaps I mean
ah: I think what we want is that for any ground mesh, there is an easy connection to its remap, and you can edit that. And then there is a button that copies the settings there to all the other ground meshes.

what then do we want to control for the ground?
the remap already deals with the total amount of contrast (by adjusting output values)
I guess I’ll just have weight and offset


ok so lightness =
base lightness + lightness offset + 2 * (luminance - 0.5) * contrast



TODO 3/19: make it so you can select a palette or a map
add the button to set all ground remaps (?? probably not necessary)

ok so you can select…
a palette
a palette settings file
a map


I guess I want a file that creates a facet settings file or something lol
select a palette and then um not sure



ok so now the buttons are…


set camera
—
make collage shader
make ground shader
—
make facet settings
make palette settings
make map template
—
make illuminee
reconnect illuminee to global
reload illuminees
—
add light
exclude light
reset light
—
load reference
—
system check

facet



TODO
    when you make facet settings file, it should give a relative path
    seems like ground light offset isn’t doing anything
    give ground AP separate settings from object AP
    applying a shader should only turn the object into an illuminee if it isn’t already part of one
    make the texture scaling normally proportional
    fix issue of ground dot
    put orienters in group
if number of facets changes, orienters cause an index error




ok now after a very long time I’m returning to this
need to make sure that band shader is calculating the lightness in the same way as a UV shader is
and need to figure out why for the UV shader I turned it into an illuminee in a sneaky way


figure out how it works with lighting at the moment
then add the ability to generate the displacement
(start as a separate script?)


want to do a test: bake lighting and use it for an object with displacement.
on the surface shader non band grass



## 2/17

hmm how are these paths working?
where does it need the scene path? maybe that has to be a string attribute
ok so
maybe just have a string attr for the obj itself, just so I don’t have to dig into the shading nodes.
(& what about the base? is that a string attr or just a )

ok I need better wording
luminance, lighting, etc

luminance: the actual luminance in the scene
live scene lighting: the normalized luminance
recorded scene lighting: the recorded lighting (based on the normalized luminance)
scene lighting: a value that could be either of the two above
base lighting: the base lighting
lighting: any of these + the base

ok how do palettes work again… why did I need to do that for loop?

ok now for atm.p.

