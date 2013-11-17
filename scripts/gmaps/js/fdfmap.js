(function (global) {

function unpack(format, packed, offset) {
    var values = [];
    var sym;
    for(var i=0; i < format.length; i++) {
        sym = format.charAt(i);

        switch(sym) {
            case 'i':   // int32, 4 bytes
                values = values.concat(packed.getSigned(32, offset));
                offset += 4;
                break;
            case 'I':   // uint32, 4 bytes
                values = values.concat(packed.getUnsigned(32, offset));
                offset += 4;
                break;
            case 'B':   // unsighed char, 1 byte
                values = values.concat(packed.getUnsigned(8, offset));
                offset += 1;
                break;
            case 'H':   // unsigned short, 2 bytes
                values = values.concat(packed.getUnsigned(16, offset));
                offset += 2;
                break;
        }
    }

    return values;
}

function FDFMap(map) {

    this.packed = map;  // jDataViewer object
    this.coordTileMap = [];

    this.negativeVersion = 0;
    this.numberOfTiles = 0;
    this.tileWidth = 0;
    this.tileHeight = 0;
    this.numMapLayers = 0;
    this.mapLayerWidthInTiles = 0;
    this.mapLayerHeightInTiles = 0;

    this.tileID = false;
    this.RLE = false;
}

FDFMap.prototype = {

tileAt: function (zlevel, x, y) {
    var tileNum = (x * this.mapLayerHeightInTiles) + y;

    layer = this.coordTileMap[zlevel];

    var num = 0;
    for(var i = 0; i < layer.length; i++) {
        if(tileNum < num + layer[i][0]) {
            return layer[i][1];
        }
        num += layer[i][0];
    }

    return -1;
},

read_metadata: function (start) {

    var metadata = unpack('iiiii', this.packed, start);

    this.negativeVersion = metadata[0];
    this.numberOfTiles   = metadata[1];
    this.tileWidth       = metadata[2];
    this.tileHeight      = metadata[3];
    this.numMapLayers    = metadata[4];

    if(this.negativeVersion < -1) {
        var featureBitFlags = -1 - this.negativeVersion;
        if(featureBitFlags & 0x01) {
            this.tileID = true;
        }
        if(featureBitFlags & 0x02) {
            this.RLE = true;
        }
    }

    return start + 20;
},

read_zlevels: function(start) {

    read_pointer = start;

    for(var i = 0; i < this.numMapLayers; i++) {
        layermeta = unpack('iii', this.packed, read_pointer);
        read_pointer += 12;

        // (depth, width, height)
        this.mapLayerWidthInTiles = layermeta[1];
        this.mapLayerHeightInTiles = layermeta[2];
    }

    return read_pointer;
},

read_tiles: function(start) {
    read_pointer = start;

    for(var i = 0; i < this.numberOfTiles; i++) {
        if(this.tileID) {
            var tileid = unpack('BBB', this.packed, read_pointer);
            read_pointer += 3;

            // (character code, bg, fg)
        }

        var numPixels = 0;
        var pixel_size = this.tileWidth * this.tileHeight;
        while(numPixels < pixel_size) {
            var pixel_rle = unpack('BBBB', this.packed, read_pointer);
            read_pointer += 4;

            // (red, green, blue)

            numPixels += pixel_rle[0];
        }
    }

    return read_pointer;
},

read_zlevel_data: function(start) {
    read_pointer = start;

    var varsize;
    if(this.RLE) {
        if(this.numberOfTiles <= 127) {
            varsize = 1;
        } else if(this.numberOfTiles <= 32767) {
            varsize = 2;
        } else {
            varsize = 4;
        }
    } else {
        if(this.numberOfTiles <= 255) {
            varsize = 1;
        } else if(this.numberOfTiles <= 65535) {
            varsize = 2;
        } else {
            varsize = 4;
        }
    }

    for(var layer = 0; layer < this.numMapLayers; layer++) {

        var zlevel = [];

        var numTiles = 0;

        var tileIndexAndFlag;
        var tileImageIndex;
        var flag = false;
        var rleTiles = 0;
        while(numTiles < this.mapLayerWidthInTiles * this.mapLayerHeightInTiles) {
            if(this.RLE) {
                switch(varsize) {
                    case 1:
                        tileIndexAndFlag = unpack('B', this.packed, read_pointer)[0];
                        flag = tileIndexAndFlag & 0x80;
                        break;
                    case 2:
                        tileIndexAndFlag = unpack('H', this.packed, read_pointer)[0];
                        flag = tileIndexAndFlag & 0x8000;
                        break;
                    case 4:
                        tileIndexAndFlag = unpack('I', this.packed, read_pointer)[0];
                        flag = tileIndexAndFlag & 0x80000000;
                        break;
                }
                read_pointer += varsize;

                if(flag) {
                    tileImageIndex = tileIndexAndFlag - flag;
                    rleTiles = unpack('B', this.packed, read_pointer)[0];
                    read_pointer += 1;

                    numTiles += rleTiles;

                    zlevel[zlevel.length] = [rleTiles, tileImageIndex]
                } else {
                    tileImageIndex = tileImageAndFlag;
                    numTiles += 1;

                    zlevel[zlevel.length] = [1, tileImageIndex]
                }
            } else {
                switch(varsize) {
                    case 1:
                        tileImageIndex = unpack('B', this.packed, read_pointer)[0];
                        break;
                    case 2:
                        tileImageIndex = unpack('H', this.packed, read_pointer)[0];
                        break;
                    case 4:
                        tileImageIndex = unpack('I', this.packed, read_pointer)[0];
                        break;
                }
                read_pointer += varsize;

                numTiles += 1;

                zlevel[zlevel.length] = [1, tileImageIndex]
            }
        }

        this.coordTileMap[layer] = zlevel;
    }

    return read_pointer;
},

process: function() {
    var read_pointer = this.read_metadata(0);                                                                                                                
    read_pointer = this.read_zlevels(read_pointer);                                                                                                          
    read_pointer = this.read_tiles(read_pointer);                                                                                                            
    this.read_zlevel_data(read_pointer);                                                                                                                     
},
};

if (typeof module !== 'undefined' && typeof module.exports === 'object') {
        module.exports = FDFMap;
} else
if (typeof define === 'function' && define.amd) {
        define([], function () { return FDFMap });
} else {
        var oldGlobal = global.FDFMap;
        (global.FDFMap = FDFMap).noConflict = function () {
                global.FDFMap = oldGlobal;
                return this;
        };
}

})((function () { return this; })());
