function initialize(mapname, fdf, start_level, startx, starty) {
  var numMapLayers = fdf.numMapLayers;

  fetched = new Grid();
  tiler = new Tiler(document.getElementById('map-canvas'), {
    tileSize: 16,
    margin: 25,
    x: startx,
    y: starty,

    fetch: function(tofetch) {
      tofetch.forEach(function(tile) {
        var x = tile[0];
        var y = tile[1];

        if (x < 0 || x >= fdf.mapLayerWidthInTiles) {
          return;
        }

        if (y < 0 || y >= fdf.mapLayerHeightInTiles) {
          return;
        }

        if (fetched.get(x, y)) {
          return tiler.show(x, y, fetched.get(x, y));
        }

        var tileId = fdf.tileAt(start_level, x, y);

        if (tileId == -1) {
          return;
        }

        var tileImageData = tileCache[tileId];
        if (tileImageData == null) {
            var tileData = fdf.getTile(tileId);

            var tile = document.createElement('canvas');
            var tileWidth = tile.width = fdf.tileWidth;
            var tileHeight = tile.height = fdf.tileHeight;
            var ctx = tile.getContext('2d');
            var imageData = ctx.getImageData(0, 0, tileWidth, tileHeight);
            var buf8 = new Uint8ClampedArray(tileData.buffer);
            imageData.data.set(buf8);

            ctx.putImageData(imageData, 0, 0);

            tileCache[tileId] = tileImageData = tile.toDataURL();
        }

        var img = new Image();
        img.onload = function() {
            var tile = $('<img/>').attr('src', img.src);

            tiler.show(x, y, tile);
            fetched.set(x, y, tile);
        };
        img.src = tileCache[tileId];
      });
    },
  });
  tiler.refresh();

  tiler.grid.draggable();
  tiler.grid.bind('drag', function() {
     tiler.refresh();
  });
  $(window).resize(function() {
     tiler.refresh();
  });
}
