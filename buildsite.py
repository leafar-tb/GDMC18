from __future__ import division
import random
import numpy as np
from collections import defaultdict
from types import FunctionType
from pymclevel import BoundingBox, ChunkNotPresent
from pymclevel.biome_types import biome_types

from myglobals import *
import boxutils as bu
from farming import chooseCrops

########################################################################

class Plot(BoundingBox):

    def __init__(self, site, box):
        super(Plot, self).__init__(box)
        self.site = site

        self.neighbours = []
        self.tags = []

    @property
    def level(self):
        return self.site.level

    @property
    def area(self):
        "The plot's floor area"
        return self.width * self.length

    @property
    def excentricity(self):
        "Distance of the plot's center to the site center, normalised to the size of the site"
        bounds = self.site.bounds
        extents = max( bounds.width/2, bounds.length/2 )
        return min( bu.centerDistance( self, bounds ) / extents, 1 )

    @property
    def centricity(self):
        return 1 - self.excentricity

    def hasNeighbourWithTag(self, tag):
        return any( tag in nbr.tags for nbr in self.neighbours )

    def neighboursWithTag(self, tag):
        return filter( lambda p: tag in p.tags, self.neighbours )

###############################

def fillInPlotNeighbours(plotList, neighboursTouch=True, neighboursOverlap=False):
    for plot in plotList:
        for otherPlot in plotList:
            if otherPlot is plot:
                continue
            if ( bu.doTouch(plot, otherPlot) and neighboursTouch ) or ( bu.doOverlap(plot, otherPlot) and neighboursOverlap ):
                plot.neighbours.append(otherPlot)

def filterByTag(plotList, *tags, **kwargs):
    quantifier = kwargs.get('quantifier', any)
    filterPredicate = lambda plot: quantifier( tag in plot.tags for tag in tags )
    return filter(filterPredicate, plotList)

########################################################################

def splitIntoPlots(site):
    backlog = [site.bounds]
    results = []
    minDim = site.minPlotDim

    def newPlot(box):
        plot = Plot(site, box)
        results.append(plot)
        return plot

    while backlog:
        plotBox = backlog.pop()

        if random.random() < .1 and plotBox.width < site.maxPlotDim and plotBox.length < site.maxPlotDim:
            newPlot(plotBox)
            continue

        axes = [0, 2]
        random.shuffle(axes) # check x/z axes in random order
        didSplit = False
        for axis in axes:
            extraSpace = plotBox.size[axis] - minDim*2
            if extraSpace <= 0: # too small to split
                continue

            # split bigger plot with larger roads
            if extraSpace < 2*minDim:
                gapWidth = 1
            elif extraSpace < 4*minDim:
                gapWidth = 3
            else:
                gapWidth = 5
            randomSplitPos = random.randrange(minDim, plotBox.size[axis]-minDim-gapWidth+1)

            plot1, road, plot2 = splitWithGap(plotBox, axis, randomSplitPos, gapWidth)
            backlog.append(plot1)
            backlog.append(plot2)
            newPlot(road).tags.append("road" if gapWidth > 1 else "gap")
            didSplit = True
            break

        if not didSplit:
            newPlot(plotBox)

    return results

def splitWithGap(box, axis, position, gapWidth):
    plot1, plot2 = bu.splitAlongAxisAt(box, axis, position)
    gap, plot2 = bu.splitAlongAxisAt(plot2, axis, gapWidth)
    return plot1, gap, plot2

########################################################################

class WeightDict(dict):

    def __init__(self, default, basedict={}):
        super(WeightDict, self).__init__(basedict)
        self.default = default

    def random(self):
        norm = float(sum(self.values()))
        keys = self.keys()
        if norm:
            return np.random.choice( keys, p = [self[key]/norm for key in keys] )
        else:
            return self.default

    def mostCommon(self):
        if not self or not sum(self.values()):
            return self.default
        maxWeight = max(self.values())
        for key, weight in self.items():
            if maxWeight == weight:
                return key

    def leastCommon(self):
        if not self or not sum(self.values()):
            return self.default
        minWeight = min(self.values())
        for key, weight in self.items():
            if minWeight == weight:
                return key

    def weight(self, key):
        if self.isNonZero(key): # also ensures we don't div by 0
            return self[key] / float(sum(self.values()))
        return 0

    def weightedItems(self):
        return ( (key, self.weight(key)) for key in self.keys() )

    def isNonZero(self, key):
        return key in self and self[key] != 0

    def hasNonZero(self):
        return any( weight != 0 for weight in self.values() )

########################################################################

def countMaterialsIn(level, box):
    # counting block by block is too much overhead, so we process full chunks
    # this approach may not match the given bounds exactly, though
    tmpMatDict = defaultdict(int)
    for cx, cz in box.chunkPositions:
        try:
            chunk = level.getChunk(cx, cz)
        except ChunkNotPresent:
            continue
        # we first use (ID, data) tuples as material identifiers
        for ui in zip( chunk.Blocks[:, :, box.miny:box.maxy].flat, chunk.Data[:, :, box.miny:box.maxy].flat ):
            tmpMatDict[ui] += 1

    # actually, we want to return the material objects (class Block from pymclevel/materials.py)
    # looking up the materials after aggregation significantly reduces the number of queries
    matDict = WeightDict(materials.Air)
    for matTuple in tmpMatDict:
        matObj = materials[matTuple]
        assert matObj not in matDict # different IDs mapped to the same material?!
        matDict[ matObj ] = tmpMatDict[ matTuple ]

    return matDict

########################################################################

def woodTypes(site):
    counts = defaultdict(int)
    for material in site.blockCounts:
        if ' Wood ' in material.name:
            type = material.name.split(' Wood ')[0]
            counts[type] += site.blockCounts[material]
    return WeightDict('Oak', counts)

STONE_TYPES = [ materials[name] for name in ['Stone', 'Granite', 'Diorite', 'Andesite', 'Sandstone', 'Cobblestone', 'Moss Stone'] ]

def weightDictFor(default, blockTypes):
    def apply(site):
        weights = WeightDict(default)
        for block in blockTypes:
            if block in site.blockCounts:
                weights[block] = site.blockCounts[block]
        return weights
    return apply

########################################################################

DefaultSiteInfo = (
    ('stoneTypes'    , weightDictFor(materials.Stone, STONE_TYPES)),
    ('woodTypes'     , woodTypes),
    ('season'        , lambda _: random.choice(['spring', 'summer', 'autumn', 'winter'])),
    ('minPlotDim'    , 5),
    ('maxPlotDim'    , 20),
    ('crops'         , chooseCrops),
)

def fastHeightAt(level, (x,y,z), ignoreIDs):
    cx = x >> 4
    cz = z >> 4
    xInChunk = x & 0xf
    zInChunk = z & 0xf
    try:
        chunkSlice = level.getChunk(cx, cz).Blocks[xInChunk, zInChunk, :]
    except ChunkNotPresent:
        return y
    # go down until we hit ground
    while chunkSlice[y] in ignoreIDs and y > 0:
        y -= 1
    # go up until there is no ground above
    while chunkSlice[y+1] not in ignoreIDs and y+1 < level.Height:
        y += 1
    return y

class Site(object):

    def __init__(self, level, siteBox, registrar=splitIntoPlots, **kwargs):
        self.level = level
        self.bounds = siteBox
        # for the block statistics, expand vertically, so we get a better view of above- and underground features
        #? could also expand horizontally, to consider surroundings
        self.blockCounts = countMaterialsIn( level, siteBox.expand(dx=0, dy=16, dz=0) )

        # cache ground/surface heights for faster access
        self.floor = bu.floor2D(siteBox)

        NON_GROUND_IDS = set( block.ID for block in NON_GROUND_BLOCKS )
        self.groundHeights = np.array( list(
            list( fastHeightAt(level, (x, siteBox.maxy, z), NON_GROUND_IDS) for x in range(siteBox.minx, siteBox.maxx) )
                for z in range(siteBox.minz, siteBox.maxz) ) )

        NON_SURFACE_IDS = set( block.ID for block in NON_SURFACE_BLOCKS )
        self.surfaceHeights = np.array( list(
            list( fastHeightAt(level, (x, self.groundHeights[z-siteBox.minz][x-siteBox.minx], z), NON_SURFACE_IDS) for x in range(siteBox.minx, siteBox.maxx) )
                for z in range(siteBox.minz, siteBox.maxz) ) )

        # gather biome information; biomes are stored as an ID; mapping is found in pymclevel/biome_types.py or online
        tmpBiomeDict = defaultdict(int)
        for cpos in siteBox.chunkPositions:
            try:
                chunk = level.getChunk(*cpos)
            except ChunkNotPresent:
                continue
            uniques, counts = np.unique(chunk.Biomes, return_counts = True)
            for ui, ci in zip(uniques, counts):
                tmpBiomeDict[ui] += ci
        self.biomes = WeightDict(1, tmpBiomeDict) # Biome(1) = Plains
        print 'biomes =', map( lambda bID: "%s(%d): %d" % (biome_types[bID], bID, self.biomes[bID]), self.biomes )

        # compile temperature info; range is [-0.5, 2.0]
        # mostly taken from from MC wiki; actual temperature also linked to height
        TEMPERATURE_BY_BIOME = ( [ # basic biomes
                .5, .8,   2,  .2, .7, .25,  .8,  .5,
                 0,  0,  .0,  .0, .0,  .0,  .9,  .9,
                .8,  2,  .7, .25, .2, .95, .95, .95,
                .5, .2, -.5,  .6, .6,  .7, -.5, -.5,
                .3, .3,  .2, 1.2,  1,   2,   2,   2
            ] + [0]*(128-40) ) * 2 # padd with 0 for undefined biome IDs and duplicate full list to cover 'mutated' biomes
        # if temp <= 0.15: snow (and ice) possible
        # if 0.15 < temp < 1: rain possible
        # if 1 <= temp: no precipitation
        self.temperature = sum( TEMPERATURE_BY_BIOME[biome] * weight for biome, weight in self.biomes.weightedItems() )
        print 'temperature =', self.temperature

        # fraction of tiles with water at the surface
        self.surfaceWaterRatio = np.sum( (self.surfaceHeights - self.groundHeights).view(dtype=bool) ) / float(self.floor.size)
        print 'surfaceWaterRatio =', self.surfaceWaterRatio

        # could be more strict and only consider grass and dirt
        FERTILE_BLOCKS = materials.Grass, materials.Dirt, materials["Mycelium"], materials["Podzol"], materials["Coarse"]
        # typical dirt layers seem to be 3-4 blocks deep; !! normalise against floor area of blockCount
        self.fertileGroundRatio = sum( self.blockCounts.get(mat, 0) for mat in FERTILE_BLOCKS ) / ( 3.5 * self.floor.size )
        print 'fertileGroundRatio =', self.fertileGroundRatio

        # set up general site infos
        for key, val in DefaultSiteInfo:
            val = kwargs.get(key, val)
            if isinstance(val, FunctionType):
                val = val(self)
                print key, '=', val
            setattr( self, key, val )

        # split into plots
        self.plots = registrar(self)
        fillInPlotNeighbours(self.plots)

    def groundHeightAt(self, pos):
        x, z = self.floor.project(pos)
        if x in range(self.bounds.width) and z in range(self.bounds.length):
            return self.groundHeights[z][x]
        else:
            return self.level.groundPositionAt(pos, ignoreBlocks=NON_GROUND_BLOCKS).y

    def groundPositionAt(self, (x,y,z)):
        return Vector(x, self.groundHeightAt((x,y,z)), z)

    def groundPositions(self, box):
        return map(self.groundPositionAt, bu.ceiling(box).positions )

    def surfaceHeightAt(self, pos):
        x, z = self.floor.project(pos)
        if x in range(self.bounds.width) and z in range(self.bounds.length):
            return self.surfaceHeights[z][x]
        else:
            return self.level.groundPositionAt(pos, ignoreBlocks=NON_SURFACE_BLOCKS).y

    def surfacePositionAt(self, (x,y,z)):
        return Vector(x, self.surfaceHeightAt((x,y,z)), z)

    def surfacePositions(self, box):
        return map(self.surfacePositionAt, bu.ceiling(box).positions )

    def waterDepthAt(self, pos):
        return self.surfaceHeightAt(pos) - self.groundHeightAt(pos)
