from myglobals import *
from buildsite import WeightDict


class Stone:

    def __init__(self, block):
        if block.name == 'Stone':
            self.baseBlock = materials.Cobblestone
            self.refinedBlock = block
        else:
            self.baseBlock = block
            self.refinedBlock = materials['Polished ' + block.name]

        self.stairID = materials["Stone Brick Stairs (Bottom, East)"].ID
        # materials["Cobblestone Stairs (Bottom, East)"].ID

########################################################################

class Wood:

    def __init__(self, name):
        self.baseBlock = materials[name + " Wood (Bark Only)"]
        self.refinedBlock = materials[name + " Wood Planks"]
        self.stairID = materials[name + " Wood Stairs (Bottom, East)"].ID

########################################################################

class Sandstone:

    def __init__(self, prefix):
        'prefix needs to be "Red " or empty string'
        self.baseBlock = materials[prefix + "Sandstone"]
        self.refinedBlock = materials["Smooth " + prefix + "Sandstone"]
        self.stairID = materials[prefix + "Sandstone Stairs (Bottom, East)"].ID

########################################################################

class Bricks:

    def __init__(self):
        self.baseBlock = materials.Brick
        self.refinedBlock = materials.Brick
        self.stairID = materials["Brick Stairs (Bottom, East)"].ID

########################################################################
########################################################################

def chooseBuildMats(site):
    retVal = WeightDict(Stone(materials.Stone))
