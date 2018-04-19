import random
import math
from pymclevel import BoundingBox

from myglobals import *
import boxutils as bu
from types import MethodType

class Crop:

    def __init__(self, minTemperature, maxTemperature, minFertility, age0Mat, maxAge, buildFun, extraCondition=None, name=None):
        self.minTemperature = minTemperature
        self.maxTemperature = maxTemperature
        self.minFertility = minFertility
        self.age0Mat = age0Mat
        self.maxAge = maxAge
        self.grow = MethodType(buildFun, self) # buildFun(crop, plot) is exposed as self.grow(plot)
        self.extraCondition = extraCondition
        self.name = name if name is not None else self.age0Mat.name.split(' ')[0]

    def canGrow(self, site):
        if self.extraCondition is None or self.extraCondition(site):
            return site.temperature >= self.minTemperature and site.temperature <= self.maxTemperature and site.fertileGroundRatio >= self.minFertility
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

########################################################################
# construction
########################################################################

FENCE_GATE_DATA = {
    Direction.South : 0,
    Direction.West  : 1,
    Direction.North : 2,
    Direction.East  : 3,
}

def placeFenceGate(plot, woodName):
    fenceGateMat = materials[woodName+" Fence Gate (Closed, South)"]

    #TODO align gate to road or town centre?
    gateDir = random.choice(COMPASS_DIRECTIONS)
    gateWall = bu.wall2D(plot, gateDir)
    x, y, z = gateWall[gateWall.width/2, 0]
    y = plot.site.surfaceHeightAt((x, y, z))
    plot.level.setMaterialAt((x, y+1, z), (fenceGateMat.ID, FENCE_GATE_DATA[gateDir]) )
    plot.level.setMaterialAt((x, y+2, z), materials.Air )

def buildWoodFence(plot):
    woodName = plot.site.woodTypes.random()
    fenceMat = materials[woodName+" Fence"]

    for wall in bu.walls(plot):
        for (x,y,z) in plot.site.surfacePositions(wall):
            plot.level.setMaterialAt((x,y+1,z), fenceMat)
    placeFenceGate(plot, woodName)


def buildHedgeFence(plot):
    woodName = plot.site.woodTypes.random()
    hedgeMat = materials[woodName+" Leaves (No Decay)"]
    fenceGateMat = materials[woodName+" Fence Gate (Closed, South)"]

    for wall in bu.walls(plot):
        for (x,y,z) in plot.site.surfacePositions(wall):
            plot.level.setMaterialAt((x,y+1,z), hedgeMat)
            plot.level.setMaterialAt((x,y+2,z), hedgeMat)

    placeFenceGate(plot, woodName)

SOIL_WET = materials["Farmland (Wet, Moisture 7)"]
SOIL_DRY = materials["Farmland (Dry, Moisture 6)"] # moisture value doesn't change visuals

SEASON_MIN_AGE = {
    'spring' : .0,
    'summer' : .2,
    'autumn' : .7
}
SEASON_MAX_AGE = {
    'spring' : .3,
    'summer' : .8,
    'autumn' : 1.
}

def standardField(crop, plot):
    season = plot.site.season
    #TODO consider temperature
    if season == 'winter':
        soil = materials.Dirt
        cropMats = materials.Air,
    else:
        soil = SOIL_WET if plot.site.surfaceWaterRatio > .1 else SOIL_DRY
        minAge = int( math.floor( crop.maxAge * SEASON_MIN_AGE[season] ) )
        maxAge = int( math.ceil( crop.maxAge * SEASON_MAX_AGE[season] ) )
        cropMats = list( (crop.age0Mat.ID, age) for age in range(minAge, maxAge+1) )

    random.choice([buildWoodFence, buildHedgeFence, lambda _: None])(plot)
    for ground in plot.site.surfacePositions(plot.expand(-1, 0, -1)):
        plot.level.setMaterialAt(ground, soil)
        plot.level.setMaterialAt(ground+Direction.Up, random.choice(cropMats))

########################################################################

def chebyshevDist((x1,y1), (x2,y2)):
    return max( abs(x1-x2), abs(y1-y2) )

def randomSpacedPositions(plot, minSpacing):
    entityArea = (2*minSpacing + 1)**2 # square with center tile and minSpacing free tiles in both directions
    floorArea = plot.width * plot.length
    entityCount = floorArea / float (entityArea)

    positions = [ (random.randrange(plot.width), random.randrange(plot.length)) for _ in range(int( entityCount*2 )) ]

    def countConflicts(pos):
        return sum( chebyshevDist(pos, other) <= minSpacing for other in positions if other is not pos )

    while any( countConflicts(pos) > 0 for pos in positions ):
        positions.remove( max( positions, key=countConflicts ) )

    plotFloor = bu.floor2D(plot)
    return [ plotFloor[position] for position in positions ]

def placeTreeAt(site, position, woodName, trunkHeight):
    woodMat = materials[woodName+" Wood (Upright)"]
    leafMat = materials[woodName+" Leaves (No Decay)"]
    (x,y,z) = site.surfacePositionAt(position)

    crown = BoundingBox((x-1, y+trunkHeight, z-1), (3, 2, 3))
    site.level.fill(crown, leafMat)

    for h in range(trunkHeight):
        site.level.setMaterialAt((x,y+1+h,z), woodMat)

def orchard(crop, plot): # only works for cocoa right now
    for pos in randomSpacedPositions(plot.expand(-1,0,-1), 1):
        height = random.choice( (3,4,4,4,4,5,5) )
        placeTreeAt(plot.site, pos, 'Jungle', height )

        def growAtHeight(h):
            surfPos = plot.site.surfacePositionAt(pos)
            growDir = random.choice(COMPASS_DIRECTIONS)
            growPos = surfPos + (0, h, 0) + growDir
            fruitMat = crop.age0Mat[growDir]
            age = random.randrange(0, crop.maxAge+1)
            plot.level.setMaterialAt( growPos, (fruitMat.ID, fruitMat.blockData + age*4) )

        if height > 3 and random.random() < .75:
            growAtHeight(3)
        if height > 4 and random.random() < .75:
            growAtHeight(4)

########################################################################
# crop definitions
########################################################################

WHEAT = Crop(
    minTemperature  = .5,
    maxTemperature  = .99,
    minFertility    = .9,
    age0Mat         = materials["Wheat (Age 0)"],
    maxAge          = 7,
    buildFun        = standardField
)

POTATOES = Crop(
    minTemperature  = .2,
    maxTemperature  = .99,
    minFertility    = .5,
    age0Mat         = materials["Potatoes (Age 0)"],
    maxAge          = 7,
    buildFun        = standardField
)

CARROTS = Crop(
    minTemperature  = .0,
    maxTemperature  = .99,
    minFertility    = .3,
    age0Mat         = materials["Carrots (Age 0)"],
    maxAge          = 7,
    buildFun        = standardField
)

BEETROOT = Crop(
    minTemperature  = .0,
    maxTemperature  = .99,
    minFertility    = .1,
    age0Mat         = materials["Beetroot (Age 0)"],
    maxAge          = 3,
    buildFun        = standardField
)

COCOA = Crop(
    minTemperature  = .8, # jungle is ~.95
    maxTemperature  = 1.2,
    minFertility    = .6,
    age0Mat         = {
        Direction.South : materials["Cocoa (Age 0, South)"],
        Direction.West : materials["Cocoa (Age 0, West)"],
        Direction.North : materials["Cocoa (Age 0, North)"],
        Direction.East : materials["Cocoa (Age 0, East)"],
        },
    maxAge          = 2,
    buildFun        = orchard,
    extraCondition  = lambda site: site.woodTypes.isNonZero('Jungle'),
    name            = "Cocoa",
)

########################################################################
########################################################################

#TODO cactus, papyrus / sugar cane, melon, pumpkin
#? mushrooms, flowers, hay
#? pastures: cattle, pigs, sheep, chicken, horses, rabbits
ALL_CROPS = WHEAT, POTATOES, CARROTS, BEETROOT, COCOA

def chooseCrops(site):
    return list( filter(lambda crop: crop.canGrow(site), ALL_CROPS) )
