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


MAP_LAYER_SIZE = 12

def read_zlevels(start):
    global mapLayerWidthInTiles, mapLayerHeightInTiles

    read_pointer = start
    for i in range(numMapLayers):
        mapLayerDepth, mapLayerWidthInTiles, mapLayerHeightInTiles = \
                unpack('iii', cmap[read_pointer:read_pointer + MAP_LAYER_SIZE])
        read_pointer += MAP_LAYER_SIZE

        #print "layer %2d: depth=%d, width=%d, height=%d (%d tiles)" % \
        #        (i, mapLayerDepth, mapLayerWidthInTiles, mapLayerHeightInTiles, mapLayerWidthInTiles * mapLayerHeightInTiles)

    return read_pointer


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

        #print "Total pixels: %d" % numPixels

    return read_pointer


def read_zlevel_data(start):
    global mapLayerWidthInTiles, mapLayerHeightInTiles
    read_pointer = start

    if RLE:
        if numberOfTiles <= 127:
            varsize = 1
        elif numberOfTiles <= 32767:
            varsize = 2
        else:
            varsize = 4
    else:
        if numberOfTiles <= 255:
            varsize = 1
        elif numberOfTiles <= 65535:
            varsize = 2
        else:
            varsize = 4

    for i in range(numMapLayers):
        numTiles = 0

        #print 'Map layer %d' % i

        bitmap_layers.insert(i, [])
        while numTiles < mapLayerWidthInTiles * mapLayerHeightInTiles:

            # TODO: Find a file with RLE to test the output on
            if RLE:
                if varsize == 1:
                    tileIndexAndFlag = unpack('B', cmap[read_pointer:read_pointer + varsize])[0]
                    flag = tileIndexAndFlag & 0x80
                elif varsize == 2:
                    tileIndexAndFlag = unpack('H', cmap[read_pointer:read_pointer + varsize])[0]
                    flag = tileIndexAndFlag & 0x8000
                else:
                    tileIndexAndFlag = unpack('I', cmap[read_pointer:read_pointer + varsize])[0]
                    flag = tileIndexAndFlag & 0x80000000
                read_pointer += varsize

                if flag:
                    tileImageIndex = tileIndexAndFlag - flag
                    rleTiles = unpack('B', cmap[read_pointer:read_pointer + 1])
                    read_pointer += 1

                    #print "%d of tile %d" % (rleTiles, tileImageIndex)
                    numTiles = numTiles + rleTiles
                else:
                    tileImageIndex = tileImageAndFlag
                    #print "1 of tile %d" % tileImageIndex
                    numTiles = numTiles + 1
            else:
                if varsize == 1:
                    tileImageIndex = unpack('B', cmap[read_pointer:read_pointer + varsize])[0]
                elif varsize == 2:
                    tileImageIndex = unpack('H', cmap[read_pointer:read_pointer + varsize])[0]
                else:
                    tileImageIndex = unpack('I', cmap[read_pointer:read_pointer + varsize])[0]
                read_pointer += varsize

                #print "1 of tile %d" % tileImageIndex
                tile = tiles[int(tileImageIndex)]
                bitmap_layers[i].insert(numTiles, tile)

                numTiles = numTiles + 1
        #print "Total tiles: %d" % numTiles

    return read_pointer


# TODO: make filenames configurable
def export_bitmap_layers():
    for l, layer in enumerate(bitmap_layers):
        newLayer = Image.new("RGB", [mapLayerWidthInTiles * tileWidth, mapLayerHeightInTiles * tileHeight], (255, 255, 255))
        for t, tile in enumerate(layer):
                tile = bitmap_layers[l][t]

                newTile = Image.new("RGB", [tileWidth, tileHeight], (255, 255, 255))
                pix = newTile.load()

                for y in range(tileHeight):
                    for x in range(tileWidth):
                        colors = tile[x + (tileWidth * y)]
                        pix[x, y] = colors

                row = int(t % mapLayerHeightInTiles)
                col = t // mapLayerHeightInTiles

                coord = (col * tileWidth, row * tileHeight, (col + 1) * tileWidth, (row + 1) * tileHeight)
                newLayer.paste(newTile, coord)

        print 'Writing to layer%d.bmp...' % l
        newLayer.save('layer%d.bmp' % l, 'BMP')

if __name__ == '__main__':
    with open('dfma_map', 'rb') as fdf:
        cmap = zlib.decompress(fdf.read())

    read_pointer = 0
    print "=== MAP INFO ==="
    read_pointer = read_metadata(start=read_pointer)

    print "=== ZLEVEL INFO === "
    read_pointer = read_zlevels(start=read_pointer)

    print "=== TILE INFO === "
    read_pointer = read_tiles(start=read_pointer)

    print "=== ZLEVEL DATA === "
    read_pointer = read_zlevel_data(read_pointer)

    export_bitmap_layers()
