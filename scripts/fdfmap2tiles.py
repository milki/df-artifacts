#!/usr/local/bin/python
#
# Decompress FDF-MAP compressed bitmap images
#
# File format:
#   http://mkv25.net/dfma/xdfmadev/DFMapCompressor_FileFormats_v-8.txt
#
#
###################################################

from PIL import Image
from math import floor
from struct import unpack
import itertools
import zlib

RLE = False
tileID = False

cmap = None
tiles = []
bitmap_layers = []
numMapLayers = 0
tileWidth = 1
tileHeight = 1
mapLayerWidthInTiles = 1
mapLayerHeightInTiles = 1


def read_metadata(start=0):
    global RLE, tileID
    global numberOfTiles
    global numMapLayers
    global tileWidth, tileHeight

    negativeVersion, numberOfTiles, tileWidth, tileHeight, numMapLayers = \
        unpack('iiiii', cmap[start:start + 20])

    print "%d unique tiles at %d x %d pixels" % (numberOfTiles, tileWidth, tileHeight)

    if negativeVersion < -1:
        featureBitFlags = -1 - negativeVersion
        if featureBitFlags & 0x01:
            tileID = True
        if featureBitFlags & 0x02:
            RLE = True

        print "Features: negVer=%d, tileID=%d, RLE=%d" % (negativeVersion, tileID, RLE)

    print "%d z-levels" % numMapLayers

    return start + 20

TILE_ID_SIZE = 3
PIXEL_SIZE = 4

def read_tiles(start):
    read_pointer = start
    TILE_PIXEL_SIZE = tileWidth * tileHeight

    for i in range(numberOfTiles):
        if tileID:
            characterCode, backgroundColor, foregroundColor = \
                    unpack('BBB', cmap[read_pointer:read_pointer + TILE_ID_SIZE])
            read_pointer += TILE_ID_SIZE

            #print "tile %d: code=%02X, bg=%02X, fg=%02X" % (i, characterCode, backgroundColor, foregroundColor)

        tiles.insert(i, [])
        numPixels = 0
        while numPixels < TILE_PIXEL_SIZE:
            numberOfPixels, blue, green, red = unpack('BBBB', cmap[read_pointer:read_pointer + PIXEL_SIZE])
            read_pointer += PIXEL_SIZE

            #print "%d pixels with (%02X, %02X, %02X)" % (numberOfPixels, blue, green, red)

            for p in range(numberOfPixels):
                tiles[i].append((red, green, blue))

            numPixels += numberOfPixels

    return read_pointer

def export_bitmap_tiles():
    for t, tile in enumerate(tiles):
        newTile = Image.new("RGB", [tileWidth, tileHeight], (255, 255, 255))
        pix = newTile.load()

        for y in range(tileHeight):
            for x in range(tileWidth):
                colors = tile[x + (tileWidth * y)]
                pix[x, y] = colors

        print 'Writing to tile%d.png...' % t
        newTile.save('tile%d.png' % t, 'PNG')

if __name__ == '__main__':
    with open('dfma_map', 'rb') as fdf:
        cmap = zlib.decompress(fdf.read())

    read_pointer = 0
    print "=== MAP INFO ==="
    read_pointer = read_metadata(start=read_pointer)

    print "=== ZLEVEL INFO === "
    MAP_LAYER_SIZE = 12
    read_pointer += (MAP_LAYER_SIZE * numMapLayers)

    print "=== TILE INFO === "
    read_tiles(start=read_pointer)

    export_bitmap_tiles()
