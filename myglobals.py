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

BLOCK_TYPES = [
    u'THINSLICE', u'ENDER_PORTAL_FRAME', 'NORMAL', u'LADDER', u'PISTON_HEAD',
    u'NETHER_WART', u'BED', u'WALLSIGN', u'SOLID_PANE', u'CHEST', u'HUGE_MUSHROOM', u'PORTAL',
    u'DECORATION_CROSS', u'LEAVES', u'TORCH', u'HALFHEIGHT', u'CAKE', u'SEMISOLID', u'DOOR',
    u'FLOOR', u'CROPS', u'SIGNPOST', u'VINE', u'CAULDRON', u'PISTON_BODY', u'PRESSURE_PLATE',
    u'LEVER', u'STEM', u'STAIRS', u'FENCE', u'TRAPDOOR', u'BUTTON', u'WATER', u'GLASS',
    u'ENCHANTMENT_TABLE', u'SIMPLE_RAIL', u'ENDER_PORTAL', u'FENCE_GATE'
    ]

BLOCK_TYPES_GROWTHS = [u'HUGE_MUSHROOM', u'DECORATION_CROSS', u'LEAVES', u'CROPS', u'VINE', u'STEM']

NON_GROUND_BLOCKS = materials.blocksMatching("water") + materials.blocksMatching("air") + \
    materials.blocksMatching("snow") + materials.blocksMatching("log")
for t in BLOCK_TYPES_GROWTHS:
    NON_GROUND_BLOCKS.extend( materials.blocksByType[t] )
