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

                if (x < 0 || x >= tileNum) {
                    return null;
                }

                if (y < 0 || y >= tileNum) {
                    return null;
                }

                tile = fdf.tileAt(2, x, y);
                if(tile == -1) {
                    return null;
                }

                return "tiles/tile" + tile + ".png";
            },
            tileSize: new google.maps.Size(fdf.tileHeight, fdf.tileWidth),
            minZoom: 8,
            maxZoom: 8,
            name: 'Dwarf Fortress ZLevel'
        };


        var ZLevelMapType = new google.maps.ImageMapType(ZLevelTypeOptions);

        var mapOptions = {
          center: new google.maps.LatLng(85, -180),
          zoom: 8,
          mapTypeId: 'df',
          mapTypeControlOptions: {
              mapTypeIds: ['df']
          },

          panControl:           false,
          scaleControl:         false,
          mapTypeControl:       false,
          streetViewControl:    false,
          overviewMapControl:   false,
          zoomControl:          false,
        };
        var map = new google.maps.Map(document.getElementById("map-canvas"),
            mapOptions);

        map.mapTypes.set('df', ZLevelMapType);
        map.setMapTypeId('df');
    };
    xhr.send(null);

}
google.maps.event.addDomListener(window, 'load', initialize);
