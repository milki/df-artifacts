#!/usr/local/bin/python
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

        layer = Image.open(filename)
        layer_info.append((filename, int(layer_depth), layer))

    return fort_name, layer_info


def process_layers(layers):
    global args

    tiled_layers = split_into_tiles(layers, args.tilewidth, args.tileheight)

    uniquetiles, compressed_layer_data = compress_layers(tiled_layers)

    return uniquetiles, compressed_layer_data


def split_into_tiles(layers, tilewidth, tileheight):
    tiled_layers = []
    for layer_file, _, layer in layers:
        tiles = []

        for tile_buffer in crop(layer, tilewidth, tileheight):
            tile = Image.new('RGB', [tilewidth, tileheight], 255)
            tile.paste(tile_buffer)
            tiles.append(tile)
        tiled_layers.append(tiles)
    return tiled_layers


def crop(im, width, height):
    imgwidth, imgheight = im.size
    for j in range(imgwidth//width):
        for i in range(imgheight//height):
            box = (j * width, i * height, (j + 1) * width, (i + 1) * height)
            yield im.crop(box)


def compress_layers(tiled_layers):
    unique_tiles = []
    compressed_layer_data = []

    for l, layer in enumerate(tiled_layers):
        #print "map layer %d" % l
        compressed_layer_data.insert(l, [])
        for t, tile in enumerate(layer):
            if tile.tostring() not in unique_tiles:
                unique_tiles.append(tile.tostring())
            compressed_layer_data[l].insert(t, unique_tiles.index(tile.tostring()))
            #print "1 of tile %d" % unique_tiles.index(tile.tostring())

        print "Layer %d has %d unique tiles out of %d" % (l, len(set(compressed_layer_data[l])), len(compressed_layer_data[l]))
                
    return unique_tiles, compressed_layer_data

def write_compressed_file(unique_tiles, compressed_layer_data):
    global args

    cstring = cStringIO.StringIO()

    # Headers
    print "=== MAP INFO ==="
    print "%d unique tiles at %d x %d pixels" % (len(unique_tiles), args.tilewidth, args.tileheight)
    print "Features: negVer=%d, tileID=True, RLE=False" % -2
    print "%d z-levels" % len(args.images)

    # TODO: Allow for other negativeVersions
    cstring.write(pack('iiiii', -2, len(unique_tiles), args.tilewidth, args.tileheight, len(args.images)))

    # ZLEVELS
    print "=== ZLEVEL INFO ==="
    for _, depth, layer in args.images:
        layerwidth, layerheight = layer.size

        layerwidthintiles = layerwidth//args.tilewidth
        layerheightintiles = layerheight//args.tileheight
        print "layer: depth=%d, width=%d, height=%d (%d pixels)" % (depth, layerwidthintiles, layerheightintiles, (layerwidthintiles * layerheightintiles))

        cstring.write(pack('iii', depth, layerwidth//args.tilewidth, layerheight//args.tileheight))

    # TILES
    print "=== TILE INFO ==="
    for t, tile in enumerate(unique_tiles):
        pix = Image.fromstring('RGB', [args.tilewidth, args.tileheight], tile).load()
        lastpixel = None
        pixelCount = 0
        #print 'tile %d' % t

        cstring.write(pack('BBB', 0xFF, 0xFF, 0xFF))

        for y in range(args.tileheight):
            for x in range(args.tilewidth):
                if pix[x, y] == lastpixel:
                    pixelCount += 1

                    if pixelCount == 255:
                        red, green, blue = pix[x, y]
                        cstring.write(pack('BBBB', pixelCount, blue, green, red))
                        #print "%d pixels with (%02X, %02X, %02X)" % (pixelCount, blue, green, red)
                        pixelCount = 0
                else:
                    if lastpixel is not None:
                        red, green, blue = lastpixel
                        cstring.write(pack('BBBB', pixelCount, blue, green, red))
                        #print "%d pixels with (%02X, %02X, %02X)" % (pixelCount, blue, green, red)
                    lastpixel = pix[x, y]
                    pixelCount = 1

        if pixelCount != 0:
            red, green, blue = lastpixel
            cstring.write(pack('BBBB', pixelCount, blue, green, red))
            #print "%d pixels with (%02X, %02X, %02X)" % (pixelCount, blue, green, red)



    # ZLEVEL DATA
    print "=== ZLEVEL DATA ==="
    if len(unique_tiles) <= 255:
        indexfmt = 'B'
    elif len(unique_tiles) <= 65535:
        indexfmt = 'H'
    else:
        indexfmt = 'I'

    for l, layer in enumerate(compressed_layer_data):
        print "Writing layer %d with %d tiles" % (l, len(layer))
        for tileIndex in layer:
            cstring.write(pack(indexfmt, tileIndex))

    filename = "%s.fdf-map" % args.fort
    with open(filename, 'wb') as cfile:
        cfile.write(zlib.compress(cstring.getvalue()))
        print 'Wrote %d bytes to filename %s' % (len(cstring.getvalue()), filename)

if __name__ == '__main__':
    process_command()
    unique_tiles, compressed_layer_data = process_layers(args.images)
    write_compressed_file(unique_tiles, compressed_layer_data)
    
