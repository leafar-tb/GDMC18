from types import MethodType

import boxutils as bu
from myglobals import materials, NON_GROUND_BLOCKS, Vector

# list of functions to inject
_functionsToInject = []

# decorator to add functions for injection
def injected(func):
    _functionsToInject.append(func)
    return func

def inject(level):
    for func in _functionsToInject:
        setattr( level, func.__name__, MethodType(func, level) )

########################################################################

@injected
def materialAt(level, (x,y,z)):
    return materials[ level.blockAt(x,y,z), level.blockDataAt(x,y,z) ]

@injected
def setMaterialAt(level, (x,y,z), mat):
    if isinstance(mat, (list, tuple)):
        level.setBlockAt(x, y, z, mat[0])
        level.setBlockDataAt(x, y, z, mat[1])
    else:
        level.setBlockAt(x, y, z, mat.ID)
        level.setBlockDataAt(x, y, z, mat.blockData)

########################################################################

@injected
def fill(level, box, mat):
    for point in box.positions:
        setMaterialAt(level, point, mat)

########################################################################

@injected
def groundPositionAt(level, (x,y,z), ignoreBlocks=NON_GROUND_BLOCKS):
    # go down until we hit ground
    while materialAt(level, (x,y,z)) in ignoreBlocks and y > 0:
        y -= 1
    # go up until there is no ground above
    while materialAt(level, (x,y+1,z)) not in ignoreBlocks and y+1 < level.Height:
        y += 1
    return Vector(x,y,z)

@injected
def groundPositions(level, box, doBoxClip=False, ignoreBlocks=NON_GROUND_BLOCKS):
    for pos in bu.ceiling(box).positions:
        if doBoxClip:
            yield bu.clip(groundPositionAt(level, pos, ignoreBlocks), box)
        else:
            yield groundPositionAt(level, pos, ignoreBlocks)
