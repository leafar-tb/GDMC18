from myglobals import *
from buildsite import WeightDict
from pymclevel.materials import Block

class DefaultMatBase:
    def getBaseBlock(self, orientation=Orientation.Undefined):
        return self.baseBlock

def commonness(site, blockOrCount):
    count = site.blockCounts[blockOrCount] if type(blockOrCount) is Block else blockOrCount
    commonnessValue = float(count) / (site.bounds.width * site.bounds.length) if count > 0 else 0.0
    print blockOrCount, commonnessValue
    return commonnessValue

def valueModifier(site, blockOrCount, defaultCommonness):
    commonnessValue = commonness(site, blockOrCount)
    return max(0.1, min(defaultCommonness / commonnessValue, 10)) if commonnessValue > 0 else 0.1

########################################################################

class StoneBase(DefaultMatBase):
    @classmethod
    def getForSite(cls, site):
        STONE_TYPES = [ materials[name] for name in ['Stone', 'Granite', 'Diorite', 'Andesite'] ]
        stoneMats = [ (cls(stoneType), stoneType) for stoneType in STONE_TYPES if site.stoneTypes.isNonZero(stoneType) ]
        for mat, block in stoneMats:
            mat.value *= valueModifier(site, block, 10)
        return [ mat for mat, _ in stoneMats ]

class Stone(StoneBase):
    value = 2

    def __init__(self, block):
        if block.name == 'Stone':
            self.baseBlock = materials.Cobblestone
        else:
            self.baseBlock = block
        self.stairID = materials["Cobblestone Stairs (Bottom, East)"].ID

class PolishedStone(StoneBase):
    value = 4

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
    value = 1

    @staticmethod
    def getForSite(site):
        return [ Wood(woodType, valueModifier(site, site.woodTypes[woodType], 0.01)) for woodType in site.woodTypes ]

    def __init__(self, name, vMod):
        try:
            self.baseBlock = materials[name + " Wood (Upright)"]
        except:
            self.baseBlock = materials[name + " Wood (Upright, " + name + ")"]

        self.baseBlocks = 4 * [None]
        for orientation, data in WOOD_ORIENTATION_MAP.items():
            self.baseBlocks[orientation] = materials[self.baseBlock.ID, data]
        self.stairID = materials[name + " Wood Stairs (Bottom, East)"].ID

        self.value *= vMod

    def getBaseBlock(self, orientation=Orientation.Undefined):
        return self.baseBlocks[orientation]

class WoodPlanks(DefaultMatBase):
    value = 1.5

    @staticmethod
    def getForSite(site):
        return [ WoodPlanks(woodType, valueModifier(site, site.woodTypes[woodType], 0.01)) for woodType in site.woodTypes ]

    def __init__(self, name, vMod):
        self.baseBlock = materials[name + " Wood Planks"]
        self.stairID = materials[name + " Wood Stairs (Bottom, East)"].ID
        self.value *= vMod

########################################################################

class SandstoneBase(DefaultMatBase):

    @classmethod
    def getForSite(cls, site):
        lst = []
        if site.blockCounts.isNonZero(materials["Sandstone"]):
            lst.append(cls(""))
            lst[-1].value *= valueModifier(site, materials["Sandstone"], 5)
        if site.blockCounts.isNonZero(materials["Red Sandstone"]):
            lst.append(cls("Red "))
            lst[-1].value *= valueModifier(site, materials["Red Sandstone"], 5)
        return lst

class Sandstone(SandstoneBase):
    value = 1

    def __init__(self, prefix):
        self.baseBlock = materials[prefix + "Sandstone"]
        self.stairID = materials[prefix + "Sandstone Stairs (Bottom, East)"].ID

class SmoothSandstone(SandstoneBase):
    value = 1.5

    def __init__(self, prefix):
        self.baseBlock = materials["Smooth " + prefix + "Sandstone"]
        self.stairID = materials[prefix + "Sandstone Stairs (Bottom, East)"].ID

class ChiseledSandstone(SandstoneBase):
    value = 2

    def __init__(self, prefix):
        self.baseBlock = materials["Chiseled " + prefix + "Sandstone"]
        self.stairID = materials[prefix + "Sandstone Stairs (Bottom, East)"].ID

########################################################################

class Bricks(DefaultMatBase):
    value = 1

    @staticmethod
    def getForSite(site):
        if site.blockCounts.isNonZero(materials["Clay"]):
            return [Bricks(site)]
        else:
            return []

    def __init__(self, site):
        self.baseBlock = materials.Brick
        self.stairID = materials["Brick Stairs (Bottom, East)"].ID
        self.value *= valueModifier(site, materials["Clay"], 0.05)

########################################################################
########################################################################

def getBuildMats(site):
    materialList = []
    for materialType in Stone, PolishedStone, Wood, WoodPlanks, Sandstone, SmoothSandstone, ChiseledSandstone, Bricks:
        materialList.extend( materialType.getForSite(site) )
    return materialList
