from pymclevel import alphaMaterials as materials

from pymclevel.box import Vector

class Direction:

    def __init__(self, vector):
        self.vector = Vector(vector)

    North = (( 0,  0, -1))
    East  = (( 1,  0,  0))
    South = (( 0,  0,  1))
    West  = ((-1,  0,  0))
    Up    = (( 0,  1,  0))
    Down  = (( 0, -1,  0))

COMPASS_DIRECTIONS = Direction.North, Direction.East, Direction.South, Direction.West

class Orientation:
    Upright    = 0
    EastWest   = 1
    NorthSouth = 2
    Undefined  = 3

    @staticmethod
    def of(box):
        size = box.size
        # if one dimension is largest, it determines the orientation
        if size.x > size.y and size.x > size.z:
            return EastWest
        if size.y > size.x and size.y > size.z:
            return Upright
        if size.z > size.x and size.z > size.y:
            return NorthSouth

        # if all dimensions are equal, orientation is undefined
        if size.x == size.y == size.z:
            return Undefined

        # if two dimensions are equal, the remaining one determines the orientation
        if size.x == size.y:
            return NorthSouth
        if size.y == size.z:
            return EastWest
        if size.z == size.x:
            return Upright
        assert False, "Unhandled Orientation case: " + str(size)

    @staticmethod
    def horizontalOf(box):
        size = box.size
        # if one dimension is largest, it determines the orientation
        if size.x > size.z:
            return EastWest
        if size.z > size.x:
            return NorthSouth
        return Undefined

class WeightDict(dict):

    def __init__(self, default, basedict={}):
        super(WeightDict, self).__init__(basedict)
        self.default = default

    def random(self):
        from numpy import random

        norm = float(sum(self.values()))
        keys = self.keys()
        if norm:
            return random.choice( keys, p = [self[key]/norm for key in keys] )
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

BLOCK_TYPES = [
    u'THINSLICE', u'ENDER_PORTAL_FRAME', 'NORMAL', u'LADDER', u'PISTON_HEAD',
    u'NETHER_WART', u'BED', u'WALLSIGN', u'SOLID_PANE', u'CHEST', u'HUGE_MUSHROOM', u'PORTAL',
    u'DECORATION_CROSS', u'LEAVES', u'TORCH', u'HALFHEIGHT', u'CAKE', u'SEMISOLID', u'DOOR',
    u'FLOOR', u'CROPS', u'SIGNPOST', u'VINE', u'CAULDRON', u'PISTON_BODY', u'PRESSURE_PLATE',
    u'LEVER', u'STEM', u'STAIRS', u'FENCE', u'TRAPDOOR', u'BUTTON', u'WATER', u'GLASS',
    u'ENCHANTMENT_TABLE', u'SIMPLE_RAIL', u'ENDER_PORTAL', u'FENCE_GATE'
    ]

BLOCK_TYPES_GROWTHS = [u'HUGE_MUSHROOM', u'DECORATION_CROSS', u'LEAVES', u'CROPS', u'VINE', u'STEM']

# type FLOOR is for redstone wire and lily pads
NON_SURFACE_BLOCKS  = set( [materials.Air] + materials.blocksMatching("snow") + materials.blocksMatching("log") + materials.blocksMatching("Pumpkin") + \
        materials.blocksByType["FLOOR"] + \
        list(btype for btypeClass in BLOCK_TYPES_GROWTHS for btype in materials.blocksByType[btypeClass]) )

NON_GROUND_BLOCKS = NON_SURFACE_BLOCKS.union( materials.blocksMatching("water") ).union( [ materials.Ice, materials.PackedIce, materials.FrostedIce ] )
