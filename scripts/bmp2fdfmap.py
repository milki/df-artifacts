#!/usr/bin/python
#
# Compress DF bitmap images to FDF-MAP
#
# File format:
#   http://mkv25.net/dfma/xdfmadev/DFMapCompressor_FileFormats_v-8.txt

from PIL import Image
from struct import pack
import argparse
import cStringIO
import zlib



def process_command():
    global args

    parser = argparse.ArgumentParser()
    parser.add_argument('images', nargs='+', help='Exported bmp map layers')
    parser.add_argument('--tilewidth', dest='tilewidth', type=int,
            help='Pixel width of a tile', required=True)
    parser.add_argument('--tileheight', dest='tileheight', type=int,
            help='Pixel height of a tile', required=True)

    args = parser.parse_args()

    args.fort, args.images = process_files(args.images)


def process_files(layer_files):
    # TODO: Smarter names
    fort_name = None

    layer_info = []
    for filename in layer_files:
        name, layer_depth = filename.split('-')[0:2]

        if fort_name is None:
            fort_name = name
        else:
            assert fort_name == name

        layer_info.append((filename, int(layer_depth)))

    return fort_name, layer_info


def split_and_compress_layers(layers, tilewidth, tileheight):
    unique_tiles = []
    compressed_layers = []
    for l, (layer_file, depth) in enumerate(layers):
        print "Splitting and compressing %s" % layer_file
        tiles = []

        layer = Image.open(layer_file)
        layerwidth, layerheight = layer.size

        for tile_buffer in crop(layer, tilewidth, tileheight):
            tile = Image.new('RGB', [tilewidth, tileheight], 255)
            tile.paste(tile_buffer)
            tile_str = tile.tostring()

            if tile_str not in unique_tiles:
                unique_tiles.append(tile_str)
            tiles.append(unique_tiles.index(tile_str))

            del tile
        del layer
        compressed_layers.append((layerwidth, layerheight, depth, tiles))

        print "Layer %d has %d unique tiles out of %d" % (l, len(set(compressed_layers[l][3])), len(compressed_layers[l][3]))
    return unique_tiles, compressed_layers


def crop(im, width, height):
    imgwidth, imgheight = im.size
    for j in range(imgwidth//width):
        for i in range(imgheight//height):
            box = (j * width, i * height, (j + 1) * width, (i + 1) * height)
            yield im.crop(box)


def write_compressed_file(fortname, unique_tiles, tilewidth, tileheight, compressed_layers):

    cstring = cStringIO.StringIO()

    # Headers
    print "=== MAP INFO ==="
    print "%d unique tiles at %d x %d pixels" % (len(unique_tiles), tilewidth, tileheight)
    print "Features: negVer=%d, tileID=1, RLE=1" % -4
    print "%d z-levels" % len(compressed_layers)

    # TODO: Allow for other negativeVersions
    cstring.write(pack(
        'iiiii',
        -4,
        len(unique_tiles),
        tilewidth, tileheight,
        len(compressed_layers)))

    # ZLEVELS
    print "=== ZLEVEL INFO ==="
    for width, height, depth, _ in compressed_layers:
        layerwidthintiles = width//tilewidth
        layerheightintiles = height//tileheight
        print "layer: depth=%d, width=%d, height=%d (%d pixels)" % (depth, layerwidthintiles, layerheightintiles, (layerwidthintiles * layerheightintiles))

        cstring.write(pack(
            'iii',
            depth,
            width//tilewidth,
            height//tileheight))

    # TILES
    print "=== TILE INFO ==="
    for t, tile in enumerate(unique_tiles):
        pix = Image.fromstring('RGB', [tilewidth, tileheight], tile).load()
        lastpixel = None
        pixelCount = 0
        #print 'tile %d' % t

        cstring.write(pack('BBB', 0xFF, 0xFF, 0xFF))

        for y in range(tileheight):
            for x in range(tilewidth):
                if pix[x, y] == lastpixel:
                    pixelCount += 1

                    if pixelCount == 255:
                        red, green, blue = pix[x, y]
                        cstring.write(pack(
                            'BBBB',
                            pixelCount,
                            blue, green, red))
                        #print "%d pixels with (%02X, %02X, %02X)" % (pixelCount, blue, green, red)
                        pixelCount = 0
                else:
                    if lastpixel is not None:
                        red, green, blue = lastpixel
                        cstring.write(pack(
                            'BBBB',
                            pixelCount,
                            blue, green, red))
                        #print "%d pixels with (%02X, %02X, %02X)" % (pixelCount, blue, green, red)
                    lastpixel = pix[x, y]
                    pixelCount = 1

        if pixelCount != 0:
            red, green, blue = lastpixel
            cstring.write(pack(
                'BBBB',
                pixelCount,
                blue, green, red))
            #print "%d pixels with (%02X, %02X, %02X)" % (pixelCount, blue, green, red)
        del pix


    # ZLEVEL DATA
    print "=== ZLEVEL DATA ==="
    if len(unique_tiles) <= 127:
        indexfmt = 'B'
        flag = 0x80
    elif len(unique_tiles) <= 32767:
        indexfmt = 'H'
        flag = 0x8000
    else:
        indexfmt = 'I'
        flag = 0x80000000

    for l, layer in enumerate(compressed_layers):
        print "Writing layer %d with %d tiles" % (l, len(layer[3]))

        tileCount = 0
        lastTileIndex = None
        for tileIndex in layer[3]:
            if tileIndex == lastTileIndex:
                tileCount += 1
                if tileCount == 127:
                    tileImageIndex = tileIndex | flag
                    #print '%d of tile %d' % (tileCount, tileIndex)
                    cstring.write(pack(indexfmt, tileImageIndex))
                    cstring.write(pack('B', tileCount))
                    tileCount = 0
            else:
                if lastTileIndex is not None:
                    if tileCount == 1:
                        #print '1 of tile %d' % lastTileIndex
                        cstring.write(pack(indexfmt, lastTileIndex))
                    else:
                        tileImageIndex = lastTileIndex | flag
                        #print '%d of tile %d' % (tileCount, lastTileIndex)
                        cstring.write(pack(indexfmt, tileImageIndex))
                        cstring.write(pack('B', tileCount))
                lastTileIndex = tileIndex
                tileCount = 1

        if tileCount == 1:
            #print '1 of tile %d' % lastTileIndex
            cstring.write(pack(indexfmt, lastTileIndex))
        elif tileCount > 1:
            tileImageIndex = lastTileIndex | flag
            #print '%d of tile %d' % (tileCount, lastTileIndex)
            cstring.write(pack(indexfmt, tileImageIndex))
            cstring.write(pack('B', tileCount))

    filename = "%s.fdf-map" % fortname
    with open(filename, 'wb') as cfile:
        cfile.write(zlib.compress(cstring.getvalue()))
        print 'Wrote %d bytes to filename %s' % (len(cstring.getvalue()), filename)

if __name__ == '__main__':
    process_command()
    unique_tiles, compressed_layers = \
            split_and_compress_layers(
                    args.images,
                    args.tilewidth, args.tileheight)
    write_compressed_file(
            args.fort,
            unique_tiles,
            args.tilewidth, args.tileheight,
            compressed_layers)
