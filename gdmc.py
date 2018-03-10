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

inputs = (
	(displayName, "label"),
	)

def perform(level, box, options):
    LVinject(level)

    site = Site(level, box)

    bidAndBuild(site)
