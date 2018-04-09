import random
import numpy as np
from pymclevel import BoundingBox

from myglobals import *
import boxutils as bu

def buildHouse(plot, **kwargs):
    house = House(plot, **kwargs)
    buildFoundation(house)
    buildShell(house)
    buildRoof(house)
    buildInterior(house)

########################################################################

class House:
    "The House class mostly bundles the information that is passed to the different building stages"

    def __init__(self, plot, **kwargs):
        self.plot = plot
        groundlevel = int( np.mean( [ pos.y for pos in plot.level.groundPositions(plot) ] ) )
        self.box = BoundingBox( (plot.minx, groundlevel, plot.minz), plot.size )

        # front is towards the widest road
        if not plot.hasNeighbourWithTag('road'):
            self.front = random.choice( [Direction.North, Direction.East, Direction.South, Direction.West] )
        else:
            widestRoad = max( plot.neighboursWithTag('road'), key=lambda road: min(road.width, road.length))
            self.front = bu.touchDirection(plot, widestRoad)

        # lay out the building shell
        roomHeight = kwargs.get("roomHeight", 2)
        storeySize = Vector(self.box.width, roomHeight, self.box.length)
        self.storeys = []
        self.floors = []
        nStoreys = kwargs.get("nStoreys", 2)
        # split the house into a sequence alternating between height=one floors and height=x storeys
        for s in range(nStoreys):
            self.floors.append( BoundingBox(self.box.origin + (0, s*(roomHeight+1), 0), (self.box.width, 1, self.box.length)) )
            self.storeys.append( BoundingBox(self.box.origin + (0, s*(roomHeight+1) +1, 0), storeySize) )
        # update height of bounds
        self.box = bu.expandMax(self.box, dy = nStoreys*(roomHeight+1) - self.box.height)
        # the roof is the final, topmost 'floor'
        self.roof = BoundingBox(self.box.origin + (0, nStoreys*(roomHeight+1), 0), (self.box.width, 1, self.box.length))

    @property
    def level(self):
        return self.plot.level

    @property
    def site(self):
        return self.plot.site

########################################################################
# Foundation
########################################################################

def filledFoundation(house):
    fillMat = house.site.stoneTypes.mostCommon()

    for pos in bu.floor( house.box ).positions:
        ground = house.level.groundPositionAt(pos)
        for y in range(ground.y+1, pos[1]):
            house.level.setMaterialAt((pos[0], y, pos[2]), fillMat)

####################################

def buildFoundation(house):
    #TODO different foundations; e.g. poles over water
    filledFoundation(house)

########################################################################
# Building Shell (Walls and Floors)
########################################################################

def stoneFloors(house):
    mat = house.site.stoneTypes.random()
    for flr in house.floors:
        house.level.fill(flr, mat)

def plankWalls(house):
    matName = house.site.woodTypes.random()
    mat = materials[matName+" Wood Planks"]
    for wall in bu.walls( house.box ):
        house.level.fill(wall, mat)

####################################

def buildShell(house):
    plankWalls(house)
    stoneFloors(house)

########################################################################
# Roof
########################################################################

def flatRoof(house, mat, *args):
    house.level.fill(house.roof, mat)

STAIR_DIRECTION_DATA = {
    Direction.East  : 1,
    Direction.South : 3,
    Direction.West  : 0,
    Direction.North : 2
}

def stairRoof(house, innerMat, stairMatID, fill=False):
    if house.front in [Direction.North, Direction.South]:
        steps = -1, 0, 0
        sides = [Direction.East, Direction.West]
        fronts = [Direction.North, Direction.South]
    else:
        steps = 0, 0, -1
        sides = [Direction.North, Direction.South]
        fronts = [Direction.East, Direction.West]

    roof = bu.expandMax(house.roof, dy=100)
    while roof.volume > 0 and min(roof.width, roof.length) > 1:
        layer, roof = bu.splitAlongAxisAt(roof, 1, 1)
        if fill:
            house.level.fill(layer.expand(*steps), innerMat)
        else:
            for side in fronts:
                house.level.fill( bu.wall(layer, side), innerMat )

        for side in sides:
            house.level.fill( bu.wall(layer, side), (stairMatID, STAIR_DIRECTION_DATA[side]) )

        roof = roof.expand(*steps)

    if not fill and min(roof.width, roof.length) == 1:
        layer, _ = bu.splitAlongAxisAt(roof, 1, 1)
        layer = bu.move(layer, dy=-1)
        house.level.fill( layer, innerMat )

####################################

ROOF_TYPES = [stairRoof, flatRoof]

def buildRoof(house):
    coin = random.random()
    if coin < .5:
        woodType = house.site.woodTypes.random()
        blockMat = materials[woodType+" Wood Planks"]
        stairMatID = materials[woodType+" Wood Stairs (Bottom, East)"].ID
    else:
        blockMat = materials["Bricks"]
        stairMatID = materials["Brick Stairs (Bottom, East)"].ID

    random.choice(ROOF_TYPES)(house, blockMat, stairMatID)

########################################################################
# Interior Design
########################################################################

DOOR_LOWER_DATA = {
    Direction.East  : 2,
    Direction.South : 3,
    Direction.West  : 0,
    Direction.North : 1
}

def placeDoor(level, position, direction, materialName):
    materialId = materials[materialName + ' Door (Lower, Unopened, East)'].ID
    level.setMaterialAt(position, (materialId, DOOR_LOWER_DATA[direction]))
    level.setMaterialAt(position+Direction.Up, (materialId, 8)) # 8 => upper door with unpowered left hinge

def placeWindows(level, wall):
    MAT_WINDOWS = materials["Glass"]

    wall2D = bu.BoundingBox2D(wall)
    wall2D = wall2D.expand(-1, 0) # remove corners

    if wall2D.width < 2 or wall2D.height < 2:
        return

    for x in range(0, wall2D.width-1, 3):
            level.setMaterialAt(wall2D[x, 1], MAT_WINDOWS)
            level.setMaterialAt(wall2D[x+1, 1], MAT_WINDOWS)

    if wall2D.height >= 4:
        for x in range(0, wall2D.width-1, 3):
            level.setMaterialAt(wall2D[x, 2], MAT_WINDOWS)
            level.setMaterialAt(wall2D[x+1, 2], MAT_WINDOWS)

########################################################################

def singleRoomStoreys(house):
    for i, s in enumerate( house.storeys ):
        house.level.fill(s.expand(-1, 0, -1), materials.Air) # clear interior
        for wall in bu.walls(s):
            placeWindows(house.level, wall)

        if i == 0: # ground floor has a door
            frontWall = bu.wall2D(s, house.front)
            matName = house.site.woodTypes.random()
            placeDoor( house.level, frontWall[frontWall.width/2, 0], house.front, matName )

####################################

def buildInterior(house):
    #TODO actual room layout and design
    singleRoomStoreys(house)
