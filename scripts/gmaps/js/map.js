function initialize(mapname, fdf, start_level, lat, lng) {
  var ZLevelTypes = [];
  var ZLevelTypeIds = [];

  var numMapLayers = fdf.numMapLayers;
  var mapTileWidth = fdf.mapLayerWidthInTiles;
  var mapTileHeight = fdf.mapLayerHeightInTiles;

  for(var lvl = 0; lvl < fdf.numMapLayers; lvl++) {
      var ZLevelTypeOptions = {
          getTileUrl: function(coord, zoom) {
              var tileNum = 1 << zoom;
 
              var y = coord.y
              var x = coord.x
 
              if (x < 0 || x >= mapTileWidth) {
                  return null;
              }
 
              if (y < 0 || y >= mapTileHeight) {
                  return null;
              }
 
              var tile = fdf.tileAt(this.level, x, y);
              if (tile == -1) {
                  return null;
              }
 
              return mapname + "/tile" + tile + ".png";
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
