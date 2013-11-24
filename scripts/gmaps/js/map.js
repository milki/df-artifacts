function ZLevelMapType(name, level, width, height, mapWidth, mapHeight) {
    this.height = height;
    this.width = width;
    this.mapWidth = mapWidth;
    this.mapHeight = mapHeight;
    this.name = name;
    this.level = level;
    this.tileSize = new google.maps.Size(this.height, this.width);
}

ZLevelMapType.prototype = {
    minZoom: 8,
    maxZoom: 8,
    getTile: function(coord, zoom, ownerDocument) {
        var tileNum = 1 << zoom;

        var y = coord.y
        var x = coord.x

        if (x < 0 || x >= this.mapWidth) {
            var div = ownerDocument.createElement('div');
            div.style.width = this.tileSize.width + 'px';
            div.style.height = this.tileSize.height + 'px';
            return div;
        }

        if (y < 0 || y >= this.mapHeight) {
            var div = ownerDocument.createElement('div');
            div.style.width = this.tileSize.width + 'px';
            div.style.height = this.tileSize.height + 'px';
            return div;
        }

        var tileId = fdf.tileAt(this.level, x, y);
        if (tileId == -1) {
            var div = ownerDocument.createElement('div');
            div.style.width = this.tileSize.width + 'px';
            div.style.height = this.tileSize.height + 'px';
            return div;
        }

        var img = ownerDocument.createElement('img');
        var tileImageData = tileCache[tileId];
        if (tileImageData == null) {
            var tileData = fdf.getTile(tileId);

            var tile = ownerDocument.createElement('canvas');
            var tileWidth = tile.width = this.tileSize.width;
            var tileHeight = tile.height = this.tileSize.height;
            var ctx = tile.getContext('2d');
            var imageData = ctx.getImageData(0, 0, tileWidth, tileHeight);
            var buf8 = new Uint8ClampedArray(tileData.buffer);
            imageData.data.set(buf8);

            ctx.putImageData(imageData, 0, 0);

            tileCache[tileId] = tileImageData = tile.toDataURL();
        }
        img.src = tileImageData;
        return img;
    },
    releaseTile: function(tile) { tile.remove(); },

};

function initialize(mapname, fdf, start_level, lat, lng) {
  var ZLevelTypes = [];
  var ZLevelTypeIds = [];

  var numMapLayers = fdf.numMapLayers;

  for(var lvl = 0; lvl < fdf.numMapLayers; lvl++) {
      ZLevelTypes[lvl] = new ZLevelMapType('level' + lvl, lvl, fdf.tileWidth, fdf.tileHeight, fdf.mapLayerWidthInTiles, fdf.mapLayerHeightInTiles);
      ZLevelTypeIds[lvl] = 'level' + lvl;
  }

  var mapOptions = {
    center: new google.maps.LatLng(lat, lng),
    zoom: 8,
    mapTypeId: 'level' + start_level,
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
  map.setMapTypeId('level' + start_level);
}
