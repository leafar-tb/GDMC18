from myglobals import *
from buildsite import WeightDict

class DefaultMatBase:
    def getBaseBlock(self, orientation=Orientation.Undefined):
        return self.baseBlock

########################################################################

class StoneBase(DefaultMatBase):
    @staticmethod
    def getForSite(site):
        STONE_TYPES = [ materials[name] for name in ['Stone', 'Granite', 'Diorite', 'Andesite'] ]
        return [ Stone(stoneType) for stoneType in STONE_TYPES if site.stoneTypes.isNonZero(stoneType) ]

class Stone(StoneBase):
    def __init__(self, block):
        if block.name == 'Stone':
            self.baseBlock = materials.Cobblestone
        else:
            self.baseBlock = block
        self.stairID = materials["Cobblestone Stairs (Bottom, East)"].ID

class PolishedStone(StoneBase):
    def __init__(self, block):
        if block.name == 'Stone':
            self.baseBlock = block
        else:
            self.baseBlock = materials['Polished ' + block.name]

        self.stairID = materials["Stone Brick Stairs (Bottom, East)"].ID

########################################################################

WOOD_ORIENTATION_MAP = {
    Orientation.Upright    :  0,
    Orientation.EastWest   :  4,
    Orientation.NorthSouth :  8,
    Orientation.Undefined  : 12
}

class Wood:

    @staticmethod
    def getForSite(site):
        return [ Wood(woodType) for woodType in site.woodTypes ]

    def __init__(self, name):
        try:
            self.baseBlock = materials[name + " Wood (Upright)"]
        except:
            self.baseBlock = materials[name + " Wood (Upright, " + name + ")"]

        self.baseBlocks = 4 * [None]
        for orientation, data in WOOD_ORIENTATION_MAP.items():
            self.baseBlocks[orientation] = materials[self.baseBlock.ID, data]
        self.stairID = materials[name + " Wood Stairs (Bottom, East)"].ID

    def getBaseBlock(self, orientation=Orientation.Undefined):
        return self.baseBlocks[orientation]

class WoodPlanks(DefaultMatBase):

    @staticmethod
    def getForSite(site):
        return [ WoodPlanks(woodType) for woodType in site.woodTypes ]

    def __init__(self, name):
        self.baseBlock = materials[name + " Wood Planks"]
        self.stairID = materials[name + " Wood Stairs (Bottom, East)"].ID

########################################################################

class SandstoneBase(DefaultMatBase):

    self.stairID = materials[prefix + "Sandstone Stairs (Bottom, East)"].ID

    @classmethod
    def getForSite(cls, site):
        lst = []
        if site.blockCounts.isNonZero(materials["Sandstone"]):
            lst.append(cls(""))
        if site.blockCounts.isNonZero(materials["Red Sandstone"]):
            lst.append(cls("Red "))
        return lst

class Sandstone(SandstoneBase):
    def __init__(self, prefix):
        self.baseBlock = materials[prefix + "Sandstone"]

class SmoothSandstone(SandstoneBase):
    def __init__(self, prefix):
        self.baseBlock = materials["Smooth " + prefix + "Sandstone"]

class ChiseledSandstone(SandstoneBase):
    def __init__(self, prefix):
        self.baseBlock = materials["Chiseled " + prefix + "Sandstone"]

########################################################################

class Bricks(DefaultMatBase):

    @staticmethod
    def getForSite(site):
        if site.blockCounts.isNonZero(materials["Clay"]):
            return [Bricks()]
        else:
            return []

    def __init__(self):
        self.baseBlock = materials.Brick
        self.stairID = materials["Brick Stairs (Bottom, East)"].ID

########################################################################
########################################################################

def getBuildMats(site):
    materialList = []
    for materialType in Stone, PolishedStone, Wood, WoodPlanks, Sandstone, SmoothSandstone, ChiseledSandstone, Bricks:
        materialList.extend( materialType.getForSite(site) )
    return materialList
