import numpy as np
from pymclevel import BoundingBox

from myglobals import Vector, Direction

def floor(box):
    return BoundingBox(box.origin, (box.width, 1, box.length))

def ceiling(box):
    return BoundingBox((box.minx, box.maxy-1, box.minz), (box.width, 1, box.length))

def walls(box):
    return [ wall(box, Direction.North), wall(box, Direction.East),
        wall(box, Direction.South), wall(box, Direction.West) ]

def wall(box, direction):
    if direction == Direction.North:
        return BoundingBox(box.origin, (box.width, box.height, 1))
    if direction == Direction.East:
        return BoundingBox((box.maxx-1, box.miny, box.minz), (1, box.height, box.length))
    if direction == Direction.South:
        return BoundingBox((box.minx, box.miny, box.maxz-1), (box.width, box.height, 1))
    if direction == Direction.West:
        return BoundingBox(box.origin, (1, box.height, box.length))

    # not walls as such, but close enough
    if direction == Direction.Up:
        return ceiling(box)
    if direction == Direction.Down:
        return floor(box)

def floor2D(box):
    return BoundingBox2D(floor(box))

def ceilling2D(box):
    return BoundingBox2D(ceilling(box))

def wall2D(box, direction):
    return BoundingBox2D(wall(box, direction))

def walls2D(box):
    return [ BoundingBox2D(w) for w in walls(box) ]

def clip(position, box):
    return Vector( np.clip( position, box.origin, box.maximum - Vector(1,1,1)) )

########################################################################

def expandMin(box, dx=0, dy=0, dz=0):
    return BoundingBox(box.origin - (dx,dy,dz), box.size + (dx,dy,dz))

def expandMax(box, dx=0, dy=0, dz=0):
    return BoundingBox(box.origin, box.size + (dx,dy,dz))

def move(box, dx=0, dy=0, dz=0):
    return BoundingBox(box.origin + (dx, dy, dz), box.size)

########################################################################

def splitAlongAxisAt(box, axis, position, isWorldPosition=False):
    if not isWorldPosition:
        position += box.origin[axis]

    if position <= box.origin[axis] or position >= box.maximum[axis]:
        return [box]

    size = list(box.size)
    size[axis] = position - box.origin[axis]
    b1 = BoundingBox(box.origin, size)

    origin2 = list(box.origin)
    origin2[axis] = b1.maximum[axis]
    size[axis] = box.maximum[axis] - origin2[axis]
    b2 = BoundingBox(origin2, size)

    return [b1, b2]

########################################################################

def _liesIn(val, min, max):
    return val >= min and val < max

def _doIntervalsOverlap(min1, max1, min2, max2):
    return _liesIn(min1, min2, max2) or _liesIn(max1-1, min2, max2) \
        or _liesIn(min2, min1, max1) or _liesIn(max2-1, min1, max1)

def doTouch(box1, box2):
    origin1 = box1.origin
    maximum1 = box1.maximum
    origin2 = box2.origin
    maximum2 = box2.maximum
    for axis in range(3):
        if ( origin1[axis] == maximum2[axis] or maximum1[axis] == origin2[axis] ) \
            and _doIntervalsOverlap(origin1[(axis+1)%3], maximum1[(axis+1)%3], origin2[(axis+1)%3], maximum2[(axis+1)%3]) \
            and _doIntervalsOverlap(origin1[(axis+2)%3], maximum1[(axis+2)%3], origin2[(axis+2)%3], maximum2[(axis+2)%3]):
                return True
    return False

def touchDirection(fromBox, toBox):
    if not doTouch(fromBox, toBox):
        return None

    if fromBox.maxx == toBox.minx:
        return Direction.East
    if fromBox.minx == toBox.maxx:
        return Direction.West

    if fromBox.maxy == toBox.miny:
        return Direction.Up
    if fromBox.miny == toBox.maxy:
        return Direction.Down

    if fromBox.maxz == toBox.minz:
        return Direction.South
    if fromBox.minz == toBox.maxz:
        return Direction.North

def doOverlap(box1, box2):
    return box1.intersect(box2).volume != 0

def center(box):
    return box.origin + box.size / 2

def centerDistance(box1, box2):
    return ( center(box1) - center(box2) ).length()

def minDistance(box1, box2):
    box1Center = center(box1).intfloor()
    closestInBox2ToBox1Center = clip( box1Center, box2 )
    closestInBox1ToAbove = clip( closestInBox2ToBox1Center, box1 )
    return ( closestInBox2ToBox1Center - closestInBox1ToAbove ).length()

########################################################################

class BoundingBox2D:

    def __init__(self, box):
        assert isinstance(box, BoundingBox)
        assert 1 in box.size
        self.box = box

        # try mapping x to x and y to y
        self.x_axis = 0 if box.size.index(1) != 0 else 2
        self.y_axis = 1 if box.size.index(1) != 1 else 2

    @property
    def width(self):
        return self.box.size[self.x_axis]

    @property
    def height(self):
        return self.box.size[self.y_axis]

    @property
    def size(self):
        return self.width * self.height

    @property
    def positions(self):
        return self.box.positions

    def expand(self, dx, dy):
        deltas = [0, 0, 0]
        deltas[self.x_axis] = dx
        deltas[self.y_axis] = dy
        return BoundingBox2D( self.box.expand( *deltas ) )

    def __getitem__(self, (x,y)):
        offset = [0, 0, 0]
        offset[self.x_axis] = x
        offset[self.y_axis] = y
        return self.box.origin + Vector( *offset )

    def project(self, pos3d):
        "Project a 3d position into the 2d coordinate system of this BB"
        x2d = pos3d[self.x_axis] - self.box.origin[self.x_axis]
        y2d = pos3d[self.y_axis] - self.box.origin[self.y_axis]
        return x2d, y2d
