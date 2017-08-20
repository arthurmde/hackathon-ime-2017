function initMap(lat, lng, zoom) {
  var map;
  var markers = [];

	function drawMap() {
		// Create the map.
		map = new google.maps.Map(document.getElementById('map'), {
			zoom: 4,
			center: {lat: 37.090, lng: -95.712},
			mapTypeId: 'terrain'
		});

	}

	function drawMarkers(position, color, scale){
		// Construct the circle for each value in citymap.
		// Note: We scale the area of the circle based on the population.
		var marker = new google.maps.Marker({
			position: position,
			icon: {
				path: google.maps.SymbolPath.CIRCLE,
				fillOpacity: 0.5,
				fillColor: color,
				strokeOpacity: 1.0,
				strokeColor: color,
				strokeWeight: 3.0,
				scale: scale //pixels
			},
			map: map,
		});

		marker.addListener('click', function() {
			map.setZoom(8);
			map.setCenter(marker.getPosition());
			$('.map-caption').hide();
			$('.research-detail').show();
		});

	}

	drawMap();
 	drawMarkers({lat: 49.25, lng: -123.1}, '#ff0000', 20);
 	drawMarkers({lat: 34.052, lng: -118.243}, '#fff000', 40);
}
