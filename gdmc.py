import random

from pymclevel import MCSchematic, MCLevel, BoundingBox
from mcplatform import *

from myglobals import *
import boxutils as bu
from level_extensions import inject as LVinject
from buildsite import *
from construction import bidAndBuild

# name to show in filter list
displayName = "Settlement Generator"
P_SEASON = "Season"
P_OVERRIDE_SIZE = "Override Selection Size"
P_WIDTH = "Width"
P_LENGTH = "Length"
P_HEIGHT = "Height"

inputs = (
	(displayName, "label"),
	(P_SEASON, ('random', 'spring', 'summer', 'autumn', 'winter')),
    )

def profile(func):
    import profile
    def profWrapper(*args, **kwargs):
	pr = profile.Profile()
	rVal = pr.runcall(func, *args, **kwargs)
	pr.print_stats("time")
	return rVal
    return profWrapper

def takeTime(func):
    import time
    def timeWrapper(*args, **kwargs):
	tstart = time.clock()
	rVal = func(*args, **kwargs)
	tend = time.clock()
	print func.__name__, "took", tend-tstart, "seconds"
	return rVal
    return timeWrapper

#@profile
@takeTime
def perform(level, box, options):
    LVinject(level)

    siteOptions = {}
    if options[P_SEASON] != 'random':
	siteOptions['season'] = options[P_SEASON]

    site = Site(level, box, **siteOptions)

    bidAndBuild(site)

    # due to size override, we might have been working outside the actual selection
    # but these don't seem to trigger an update
    #for cx, cz in box.chunkPositions:
    #    level.getChunk(cx, cz).dirty = True
    #level.markDirtyBox(box)
