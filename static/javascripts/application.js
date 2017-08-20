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

	function addCard(researcher) {
			var element = $('.research-detail');
			element.show();
			element.find('#name').text(researcher['name']);
			element.find('#affiliation').text(researcher['affiliation']);
			element.find('#citations').text(researcher['citations']);
			element.find('#hindex').text(researcher['hindex']);
			element.find('#email').text(researcher['email']);
			if(researcher['scholar'] === undefined) {
				element.find('#scholar').hide();
			} else {
				element.find('#scholar').show();
				element.find('#scholar').attr("href", researcher['scholar']);
			}
			element.find('#scopus').attr("href", researcher['scopus']);
	}


	function drawMarkers(researcher){
		// Construct the circle for each value in citymap.
		// Note: We scale the area of the circle based on the population.
		console.log(researcher["position"])
		var marker = new google.maps.Marker({
			position: researcher['position'],
			icon: {
				path: google.maps.SymbolPath.CIRCLE,
				fillOpacity: 0.5,
				fillColor: researcher['color'],
				strokeOpacity: 1.0,
				strokeColor: researcher['color'],
				strokeWeight: 3.0,
				scale: researcher['scale'] //pixels
			},
			map: map,
		});

		marker.addListener('click', function() {
			map.setZoom(8);
			map.setCenter(marker.getPosition());
			$('.map-caption').hide();
			addCard(researcher);
		});

	}

	var researcher_1 = {
		name: "Arthur de Moura Del Esposte",
		affiliation: "Master Degree Student, University of São Paulo",
		citations: 10,
		hindex: 1,
		email: "esposte@ime.usp.br",
		scholar: "http://temp.com",
		scopus: "http://temp.com",
		position: {lat: 49.25, lng: -123.1},
		color: '#ff0000',
		scale: 20
	};

	var researcher_2 = {
		name: "Fabio Kon",
		affiliation: "Full Professor in Computer Science, University of São Paulo",
		citations: 4500,
		hindex: 10,
		email: "kon@ime.usp.br",
		scopus: "http://temp.com",
		position: {lat: 34.053, lng: -118.243},
		color: '#fff000',
		scale: 40
	};
	drawMap();
 	drawMarkers(researcher_1);
 	drawMarkers(researcher_2);
}
