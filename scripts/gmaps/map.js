var map = null;

function initialize() {
    var fdf = null;
    var xhr= new XMLHttpRequest();
    xhr.open('GET', 'Lifelabored.fdf-map', true);
    xhr.responseType = "arraybuffer";
    xhr.onload = function(oEvent) {
        var response = new Uint8Array(xhr.response);
        var inflate = new Zlib.Inflate(response);
        var rawmap = inflate.decompress();
        var file = jDataView(rawmap, littleEndian=false);
        fdf = new FDFMap(file);

        read_pointer = fdf.read_metadata(0);
        read_pointer = fdf.read_zlevels(read_pointer);
        read_pointer = fdf.read_tiles(read_pointer);
        read_pointer = fdf.read_zlevel_data(read_pointer);

        var ZLevelTypeOptions = {
            getTileUrl: function(coord, zoom) {
                var tileNum = 1 << zoom;

                var y = coord.y
                var x = coord.x

                if (x < 0 || x >= this.mapLayerWidthInTiles = 0) {
                    return null;
                }

                if (y < 0 || y >= this.mapLayerHeightInTiles = 0) {
                    return null;
                }

                tile = fdf.tileAt(this.level, x, y);
                if(tile == -1) {
                    return null;
                }

                return "tiles/tile" + tile + ".png";
            },
            tileSize: new google.maps.Size(fdf.tileHeight, fdf.tileWidth),
            minZoom: 8,
            maxZoom: 8,
        };


        var ZLevelTypes = [];
        var ZLevelTypeIds = [];
        for(var lvl = 0; lvl < fdf.numMapLayers; lvl++) {
            var ZLevelTypeOptions = {
                getTileUrl: function(coord, zoom) {
                    var tileNum = 1 << zoom;

                    var y = coord.y
                    var x = coord.x

                    if (x < 0 || x >= tileNum) {
                        return null;
                    }

                    if (y < 0 || y >= tileNum) {
                        return null;
                    }

                    tile = fdf.tileAt(this.level, x, y);
                    if(tile == -1) {
                        return null;
                    }

                    return "tiles/tile" + tile + ".png";
                },
                tileSize: new google.maps.Size(fdf.tileHeight, fdf.tileWidth),
                minZoom: 8,
                maxZoom: 8,
            };

            ZLevelTypeOptions.name = 'level' + lvl;
            ZLevelTypeOptions.level = lvl;
            ZLevelTypes[lvl] = new google.maps.ImageMapType(ZLevelTypeOptions);
            ZLevelTypeIds[lvl] = 'level' + lvl;
        }

        var mapOptions = {
          center: new google.maps.LatLng(85, -180),
          zoom: 8,
          mapTypeId: 'level2',
          mapTypeControlOptions: {
              mapTypeIds: ZLevelTypeIds,
              style: google.maps.MapTypeControlStyle.DROPDOWN_MENU
          },
          panControl:           false,
          scaleControl:         false,
          mapTypeControl:       true,
          streetViewControl:    false,
          overviewMapControl:   false,
          zoomControl:          false,
        };

        map = new google.maps.Map(document.getElementById("map-canvas"),
            mapOptions);

        for(var i = 0; i < ZLevelTypeIds.length; i++) {
            map.mapTypes.set(ZLevelTypeIds[i], ZLevelTypes[i]);
        }
        map.setMapTypeId('level2');
    };
    xhr.send(null);

}
google.maps.event.addDomListener(window, 'load', initialize);
