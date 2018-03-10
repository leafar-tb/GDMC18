import numpy as np

from myglobals import *
import boxutils as bu

class Builder:

    def __init__(self, askInterest, awardPlot, build):
        self._askInterest = askInterest
        self._awardPlot = awardPlot
        self._build = build

    def askInterest(self, plot):
        'Return a value in [0., 1.] to indicate this builders interest in the plot.'
        return self._askInterest(plot)

    def awardPlot(self, plot):
        '''
        Informs the builder, that it is assigned this plot.
        The builder can use this to store information with the plot.
        '''
        self._awardPlot(plot)

    def build(self, plot):
        'Actually place blocks on the plot.'
        self._build(plot)

########################################################################

class BuilderCollective(Builder):

    def __init__(self, *builders):
        self.builders = builders

    def askInterest(self, plot):
        return max( b.askInterest(plot) for b in self.builders )

    def awardPlot(self, plot):
        weights = np.array( [ b.askInterest(plot) for b in self.builders ], dtype=float )
        if sum(weights) > 0:
            builder = np.random.choice( self.builders, p = (weights / sum(weights)) )
            plot.builder = builder
            builder.awardPlot(plot)

########################################################################

_registeredBuilders = []

def register(builder):
    _registeredBuilders.append(builder)

def bidAndBuild(site):
    builders = BuilderCollective(*_registeredBuilders)
    for plot in site.plots:
        if builders.askInterest(plot):
            builders.awardPlot(plot)

    for plot in site.plots:
        if hasattr(plot, 'builder'):
            plot.builder.build(plot)

########################################################################

def requires(plotPredicate):
    def decorator(askInterest):
        def inner(plot):
            if plotPredicate(plot):
                return askInterest(plot)
            else:
                return 0
        return inner
    return decorator

notARoad = lambda plot: 'road' not in plot.tags and 'gap' not in plot.tags

def minimumDimensions(minDim):
    return lambda plot: minDim <= min(plot.width, plot.length)

def maximumDimensions(maxDim):
    return lambda plot: maxDim >= max(plot.width, plot.length)

def minimumArea(area):
    return lambda plot: area <= plot.area

def maximumArea(area):
    return lambda plot: area >= plot.area

def one(plot):
    return 1

def noop(plot):
    pass

########################################################################

def roadIF(plot):
    return 1 if 'road' in plot.tags else 0

def buildRoad(plot):
    if plot.width < plot.length:
        paveplot = plot.expand(-1, 0, 0)
    else:
        paveplot = plot.expand(0, 0, -1)

    for ground in plot.level.groundPositions(paveplot):
        plot.level.setMaterialAt(ground, plot.site.stoneTypes.random())

register( Builder(roadIF, noop, buildRoad) )

########################################################################

@requires(notARoad)
@requires(minimumDimensions(5))
def houseIF(plot):
    interest = plot.centricity
    if not plot.hasNeighbourWithTag('road'):
        interest /= 10
    return interest

def markHouse(plot):
    plot.tags.append('house')

def buildHouse(plot):
    matName = plot.site.woodTypes.random()
    MAT_WALLS = materials[matName+" Wood Planks"]

    level = plot.level
    level.fill(bu.ceiling(plot), MAT_WALLS)
    level.fill(bu.floor(plot), MAT_WALLS)
    for wall in bu.walls(plot):
        level.fill(wall, MAT_WALLS)
        placeWindows(level, wall)

    placeDoor( level, Vector(plot.minx, plot.miny+1, (plot.minz + plot.maxz)/2), Direction.East, matName )

register( Builder(houseIF, markHouse, buildHouse) )

########################################################################

crops = [
    materials["Wheat (Age 7 (Max))"],
    materials["Carrots (Age 7)"],
    materials["Potatoes (Age 7)"]
]

soil = materials["Farmland (Wet, Moisture 7)"]

@requires(notARoad)
@requires(minimumDimensions(2))
def acreIF(plot):
    if plot.excentricity < .5:
        return 0
    return plot.excentricity

def buildAcre(plot):
    crop = np.random.choice(crops)
    for ground in plot.level.groundPositions(plot):
        plot.level.setMaterialAt(ground, soil)
        plot.level.setMaterialAt(ground+Direction.Up, crop)

register( Builder(acreIF, noop, buildAcre) )
register( Builder(acreIF, noop, noop) )

########################################################################

DOOR_LOWER_DATA = {
    Direction.East  : 0,
    Direction.South : 1,
    Direction.West  : 2,
    Direction.North : 3
}

def placeDoor(level, position, direction, materialName):
    materialId = materials[materialName + ' Door (Lower, Unopened, East)'].ID
    level.setMaterialAt(position, (materialId, DOOR_LOWER_DATA[direction]))
    level.setMaterialAt(position+Direction.Up, (materialId, 8)) # 8 => upper door with unpowered left hinge

def placeWindows(level, wall):
    MAT_WINDOWS = materials["Glass"]

    wall2D = bu.BoundingBox2D(wall)
    wall2D = wall2D.expand(-1, -1) # remove corners, floor and ceiling

    if wall2D.width < 2 or wall2D.height < 2:
        return

    for x in range(0, wall2D.width-1, 3):
            level.setMaterialAt(wall2D[x, 1], MAT_WINDOWS)
            level.setMaterialAt(wall2D[x+1, 1], MAT_WINDOWS)

    if wall2D.height >= 4:
        for x in range(0, wall2D.width-1, 3):
            level.setMaterialAt(wall2D[x, 2], MAT_WINDOWS)
            level.setMaterialAt(wall2D[x+1, 2], MAT_WINDOWS)
