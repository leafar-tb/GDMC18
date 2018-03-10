import random
import numpy as np
from pymclevel import BoundingBox

from myglobals import materials
import boxutils as bu

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
        norm = sum(self.values())
        keys = self.keys()
        if norm:
            return np.random.choice( keys, p = [self[key]/norm for key in keys] )
        else:
            return self.default

########################################################################

DefaultSiteInfo = {
    'stoneTypes'    : WeightDict(materials.Stone),
    'woodTypes'     : WeightDict('Oak'),
    'climate'       : 'medium',
    'season'        : 'spring',
    'minPlotDim'    : 5,
    'maxPlotDim'    : 20,
}

class Site(object):

    def __init__(self, level, siteBox, registrar=splitIntoPlots, **kwargs):
        self.level = level
        self.bounds = siteBox
        for key in DefaultSiteInfo:
            setattr( self, key, kwargs.get(key, DefaultSiteInfo[key]) )

        self.plots = registrar(self)
        fillInPlotNeighbours(self.plots)
