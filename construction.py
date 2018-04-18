import numpy as np
import random

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
    SITE_BORDER = (2, 10, 2)

    clearAboveSurface( site, site.bounds.expand(*SITE_BORDER) )

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

# roads 'degrade' outwards
ROAD_STYLES = [
    (.1, materials.Grass),
    (.2, materials["Path"]),
    (.4, materials.Gravel),
    (.6, materials.Cobblestone),
]

def buildRoad(plot):
    # pave a narrower, but longer segment
    if plot.width < plot.length:
        paveplot = plot.expand(-1, 0, 0)
        paveplot = paveplot.expand(0, 0, 1)
    else:
        paveplot = plot.expand(0, 0, -1)
        paveplot = paveplot.expand(1, 0, 0)

    pavemat = plot.site.stoneTypes.mostCommon()
    for e, mat in ROAD_STYLES:
        if plot.centricity <= e:
            pavemat = mat
            break

    for ground in plot.site.surfacePositions(paveplot):
        plot.level.setMaterialAt(ground, pavemat)

register( Builder(roadIF, noop, buildRoad) )

########################################################################

@requires(notARoad)
@requires(minimumDimensions(5))
def houseIF(plot):
    interest = plot.centricity
    if not plot.hasNeighbourWithTag('road'):
        interest /= 10.
    return interest

def markHouse(plot):
    plot.tags.append('house')

from housing import buildHouse

register( Builder(houseIF, markHouse, buildHouse) )

########################################################################

@requires(notARoad)
@requires(minimumDimensions(2))
def acreIF(plot):
    if plot.excentricity < .5:
        return 0
    if not plot.site.crops: # no matching crops found
        return 0
    return plot.excentricity

def buildAcre(plot):
    crop = random.choice(plot.site.crops)
    crop.grow(plot)

register( Builder(acreIF, noop, buildAcre) )
register( Builder(acreIF, noop, noop) )

########################################################################

def clearAboveSurface(site, box):
    level = site.level
    for ground in site.surfacePositions(box):
        for y in range(ground.y+1, box.maxy):
            level.setMaterialAt( (ground.x, y, ground.z), materials.Air )
