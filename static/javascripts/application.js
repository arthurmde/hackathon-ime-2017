function initMap(lat, lng, zoom) {
  var map;
  var markers = [];

  function drawMap() {
    var myLatLng = {lat: lat, lng: lng};
    map = new google.maps.Map(document.getElementById('map'), {
      center: myLatLng,
      zoom: zoom
    });
  }

 	drawMap();
}
