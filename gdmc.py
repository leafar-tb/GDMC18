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

P_OVERRIDE_SIZE = "Override Selection Size"
P_WIDTH = "Width"
P_LENGTH = "Length"
P_HEIGHT = "Height"

inputs = (
	(displayName, "label"),
	("\nUse these settings, to make sure the selection has a minimum size. (Mostly dev convenience)", "label"),
	(P_OVERRIDE_SIZE, True),
	(P_WIDTH, 128),
	(P_LENGTH, 128),
	(P_HEIGHT, 16),
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

    if options[P_OVERRIDE_SIZE]:
	# expand adds on both ends, so we take the half; possible one off from rounding doesn't matter
	if box.width < options[P_WIDTH]:
	    box = box.expand( (options[P_WIDTH] - box.width) / 2, 0, 0 )
	if box.height < options[P_HEIGHT]:
	    box = box.expand( 0, (options[P_HEIGHT] - box.height) / 2, 0 )
	if box.length < options[P_LENGTH]:
	    box = box.expand( 0, 0, (options[P_LENGTH] - box.length) / 2 )

    site = Site(level, box)

    bidAndBuild(site)

    # due to size override, we might have been working outside the actual selection
    # but these don't seem to trigger an update
    #for cx, cz in box.chunkPositions:
    #    level.getChunk(cx, cz).dirty = True
    #level.markDirtyBox(box)
