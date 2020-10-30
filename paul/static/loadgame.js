var congSVG = `<svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" viewBox="0 0 24 24" fill="{0}" width="36px" height="36px"><g><rect fill="none" height="24" width="24"/></g><g><g><rect height="7" width="3" x="4" y="10"/><rect height="7" width="3" x="10.5" y="10"/><rect height="3" width="20" x="2" y="19"/><rect height="7" width="3" x="17" y="10"/><polygon points="12,1 2,6 2,8 22,8 22,6"/></g></g></svg>`;
var placeSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{0}" width="18px" height="18px"><path d="M24 24H0V0h24v24z" fill="none"/><circle cx="12" cy="12" r="8"/></svg>`;
var believerSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{0}" width="36px" height="36px"><path d="M0 0h24v24H0z" fill="none"/><path d="M20.5 6c-2.61.7-5.67 1-8.5 1s-5.89-.3-8.5-1L3 8c1.86.5 4 .83 6 1v13h2v-6h2v6h2V9c2-.17 4.14-.5 6-1l-.5-2zM12 6c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z"/></svg>`;
var elderSVG = `<svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" viewBox="0 0 24 24" fill="{0}" width="36px" height="36px"><rect fill="none" height="24" width="24"/><path d="M13.5,5.5c1.1,0,2-0.9,2-2s-0.9-2-2-2s-2,0.9-2,2S12.4,5.5,13.5,5.5z M20,12.5V23h-1V12.5c0-0.28-0.22-0.5-0.5-0.5 S18,12.22,18,12.5v1h-1v-0.69c-1.46-0.38-2.7-1.29-3.51-2.52C13.18,11.16,13,12.07,13,13c0,0.23,0.02,0.46,0.03,0.69L15,16.5V23h-2 v-5l-1.78-2.54L11,19l-3,4l-1.6-1.2L9,18.33V13c0-1.15,0.18-2.29,0.5-3.39L8,10.46V14H6V9.3l5.4-3.07l0,0.01 c0.59-0.31,1.32-0.33,1.94,0.03c0.36,0.21,0.63,0.51,0.8,0.85l0,0l0.79,1.67C15.58,10.1,16.94,11,18.5,11C19.33,11,20,11.67,20,12.5 z"/></svg>`;
var playerMarker = `<svg xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 24 24" viewBox="0 0 24 24" fill="{0}" width="48px" height="48px"><g><rect fill="none" height="24" width="24"/></g><g><g/><g><circle cx="12" cy="4" r="2"/><path d="M15.89,8.11C15.5,7.72,14.83,7,13.53,7c-0.21,0-1.42,0-2.54,0C8.24,6.99,6,4.75,6,2H4c0,3.16,2.11,5.84,5,6.71V22h2v-6h2 v6h2V10.05L18.95,14l1.41-1.41L15.89,8.11z"/></g></g></svg>`;
var placeOrigin = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{0}" width="18px" height="18px"><path d="M0 0h24v24H0z" fill="none"/><path d="M0 0h24v24H0z" fill="none"/><path d="M2 12C2 6.48 6.48 2 12 2s10 4.48 10 10-4.48 10-10 10S2 17.52 2 12zm10 6c3.31 0 6-2.69 6-6s-2.69-6-6-6-6 2.69-6 6 2.69 6 6 6z"/></svg>`;
var curLocMarker;
var map;
var markers;
var maxZoom = 16;
var realtime;
var realtimeMarkers = {};
var scores;
var userData;
var tourColours = {
	'1': {'default': '#a52749', 'player': '#27a583', 'resource': '#63d7b3'},
	'2': {'default': '#8327a5', 'player': '#2749a5', 'resource': '#6174d7'},
	'3': {'default': '#6c9537', 'player': '#5F3795', 'resource': '#9063c6'},
};
var cardColour = '#FF6384';

if (!String.prototype.format) {
	String.prototype.format = function() {
		var args = arguments;
		return this.replace(/{(\d+)}/g, function(match, number) { 
			return typeof args[number] != 'undefined'
				? args[number]
				: match
			;
		});
	};
}

function colouriseSVG(svg, colour) {
	return encodeURI('data:image/svg+xml,' + svg.format(colour)).replace('#','%23');
}

function init() {
	$.when(
		$.getJSON('/static/config.json'),
		$.getJSON('/static/tours.json')
	).done(function(configRes, toursRes) {
		var config = configRes[0];
		var tours = toursRes[0];
		L.mapbox.accessToken = config.mapboxAccessToken;
		map = L.mapbox.map('map');
		//L.PM.initialize({optIn:true});
		map.setView([40.58058, 36.29883], 4);
		map.createPane("popups");
		map.getPane("popups").style.zIndex = 700;
		map.createPane("tooltips");
		map.getPane("tooltips").style.zIndex = 690;
		map.createPane("playerMarkers");
		map.getPane("playerMarkers").style.zIndex = 640;
		map.createPane("resMarkers");
		map.getPane("resMarkers").style.zIndex = 630;
		/*map.pm.addControls({
			position: 'topleft'
		});*/
		
		scores = L.control();
		scores.onAdd = function() {
			this._div = L.DomUtil.create("div", "scores");
			L.DomEvent.disableScrollPropagation(this._div);
			L.DomEvent.disableClickPropagation(this._div);
			this.update();
			return this._div;
		};
		scores.update = function (props) {
			var scoresStr;
			if (props) {
				scoresStr = "<span class='heading indigo-text text-darken-2'>My Scores</span><br/>";
				scoresStr += `<span>&#x1F9CE; ${props.score.b} &#x1F6D0; ${props.score.c} &#x1F474; ${props.score.e} &#x1F4B0; ${props.score.s} &#x1F35E; ${props.score.f}</span><br/>`;
				scoresStr += "<span class='heading indigo-text text-darken-2'>My Mission</span><br/>";
				if (props.sel_tour == '3') {
					scoresStr += `<span>&#x1F6D0; ${props.mission_done.c}/${props.mission.c} &#x1F474; ${props.mission_done.e}/${props.mission.e} &#x1F4B0; ${props.mission_done.s}/${props.mission.s}</span><br/>`;
				} else {
					scoresStr += `<span>&#x1F9CE; ${props.mission_done.b}/${props.mission.b} &#x1F6D0; ${props.mission_done.c}/${props.mission.c} &#x1F4B0; ${props.mission_done.s}/${props.mission.s}</span><br/>`;
				}
				scoresStr += "<span class='heading indigo-text text-darken-2'>Player Scores</span><br/>";
				for (var player of Object.keys(props.player_data)) {
					scoresStr += `<span class='subheading'>${player} Score</span><br/>`;
					var playerdata = props.player_data[player];
					if (playerdata.game_over) {
						scoresStr += `<span class='indigo-text text-darken-2 game-over'><span>&#x1F9CE; ${playerdata.score.b} &#x1F6D0; ${playerdata.score.c} &#x1F474; ${playerdata.score.e} &#x1F4B0; ${playerdata.score.s} &#x1F35E; ${playerdata.score.f}</span></span><br/>`;
					} else {
						scoresStr += `<span>&#x1F9CE; ${playerdata.score.b} &#x1F6D0; ${playerdata.score.c} &#x1F474; ${playerdata.score.e} &#x1F4B0; ${playerdata.score.s} &#x1F35E; ${playerdata.score.f}</span><br/>`;
					}
				}
				scoresStr += `<span class='heading indigo-text text-darken-2'>User Turn: </span>${props.userturn}`;
			} else {
				scoresStr = "loading data...";
			}
			this._div.innerHTML = scoresStr;
		}
		scores.addTo(map);
	
		var baseLayer = L.tileLayer(`https://api.tiles.mapbox.com/v3/{id}/{z}/{x}/{y}.png?access_token=${L.mapbox.accessToken}`, {
			attribution: 'Tiles © <a href="http://awmc.unc.edu/">AWMC</a>, <a href="https://creativecommons.org/licenses/by/4.0/">CC-BY-4.0</a>',
			maxZoom: 10,
			id: 'isawnyu.map-knmctlkh',
			accessToken: L.mapbox.accessToken
		}).addTo(map);
		
		var tourRoutes = {};
		var tourMarkers = {};
		for (var idx1 = 1; idx1 < 4; idx1++) {
			var tournum = idx1;
			var tourstr = tournum.toString();
			tourRoutes[tourstr] = {
				"type": "FeatureCollection",
				"features": [{
					"type": "Feature",
					"geometry": {
						"type": "LineString",
						"coordinates": []
					}
				}]
			};
			tourMarkers[tourstr] = [];
			for (var idx2 = 0; idx2 < tours[tourstr].length; idx2++) {
				if (idx2 == 0) {
					var icon = L.icon({iconUrl: colouriseSVG(placeOrigin, 'black'), iconSize: [18, 18]});
				} else if (idx2 == (tours[tourstr].length-1)) {
					var icon = L.icon({iconUrl: colouriseSVG(placeSVG, 'black'), iconSize: [0, 0], opacity: 0});
				} else if (['Sea Trial', 'Land Trial', 'Quiz'].includes(tours[tourstr][idx2].name)) {
					var icon = L.icon({iconUrl: colouriseSVG(placeSVG, cardColour), iconSize: [18, 18]});
				} else {
					var icon = L.icon({iconUrl: colouriseSVG(placeSVG, 'black'), iconSize: [18, 18]});
				}
				tourMarkers[tourstr].push(L.marker([tours[tourstr][idx2].lat, tours[tourstr][idx2].lng], {title: tours[tourstr][idx2].name, icon: icon}));
				tourRoutes[tourstr]["features"][0]["geometry"]["coordinates"].push([tours[tourstr][idx2].lng, tours[tourstr][idx2].lat]);
			}
		}
		
		$.when(
			$.getJSON(`/user/get-user-data?userId=${$('#userId').val()}`)
		).done(function(userData) {
			console.log(`Got back user data`);
			if (userData.sel_tour != '3') {
				$('#add-elder').parent().remove();
			} else {
				$('#add-elder').prop('disabled', true);
				$('#add-believer').parent().remove();
			}
			scores.update(userData);
			var icon = L.icon({iconUrl: colouriseSVG(playerMarker, tourColours[userData.sel_tour].player), iconSize: [48, 48]});
			curLocMarker = L.marker([tours[userData.sel_tour][userData.curpos].lat, tours[userData.sel_tour][userData.curpos].lng], {title: userData.username, icon: icon, pane: 'playerMarkers'}).addTo(map);
			curLocMarker.bindTooltip(userData.username, {'permanent': true, 'pane': 'tooltips'});
			for (var idx = 0; idx < tourMarkers[userData.sel_tour].length; idx++) {
				tourMarkers[userData.sel_tour][idx].bindPopup(`<div>${tourMarkers[userData.sel_tour][idx].options.title}</div>`, {'pane': 'popups'});
			}
			L.layerGroup(tourMarkers[userData.sel_tour]).addTo(map);
			var layer = L.geoJson(tourRoutes[userData.sel_tour], {
				style: function(feature) {
					return {
						stroke: true,
						color: tourColours[userData.sel_tour].default,
						weight: 5
					};
				}
				//pmIgnore: false
			}).addTo(map);
			map.fitBounds(L.geoJson(tourRoutes[userData.sel_tour]).getBounds(), {maxZoom: maxZoom});
			realtime = L.realtime(function(success, error) {
				fetch(`/get-game-state?userId=${$('#userId').val()}`)
				.then(function(response) { return response.json(); })
				.then(processGameState)
				.catch(error);
			}, {
				interval: 5 * 1000
			}).addTo(map);
			/*layer.on('pm:update', e => {
				var tourlatlng = {};
				tourlatlng[userData.sel_tour] = [];
				for (var idx = 0; idx < e.layer._latlngs.length; idx++) {
					tourlatlng[userData.sel_tour].push(e.layer._latlngs[idx]);
				}
				var convertedData = 'application/json;charset=utf-8,'+encodeURIComponent(JSON.stringify(tourlatlng));
				document.getElementById('dload-json').setAttribute('href', 'data:' + convertedData); 
				document.getElementById('dload-json').setAttribute('download', 'data.json');
			});*/
		});
	});
}

function processGameState(gameStateRes, adding_res = false) {
	$('#dice-box').hide();
	if (gameStateRes.won) {
		console.log('Game over');
		realtime.stop();
		$('.modal-content h4').html(`Game Over`);
		$('.modal-content p').html(gameStateRes.msg);
		$('#submit-button').html('OK');
		var instance = M.Modal.getInstance($('.modal').modal());
		instance.open();
	} else {
		console.log('Got back player geopts');
		var geopts = gameStateRes;
		$.when(
			$.getJSON(`/user/get-user-data?userId=${$('#userId').val()}`)
		).done(function(userData) {
			for (var idx = 0; idx < geopts.length; idx++) {
				if (geopts[idx].properties.username) {
					console.log('realtimeMarkers', realtimeMarkers);
					if (geopts[idx].properties.username == userData.username) {
						console.log('My player record');
						if (geopts[idx].properties.userturn == userData.username) {
							console.log("It's my turn!");
							$.when(
								$.getJSON(`/user/get-user-data?userId=${$('#userId').val()}`)
							).done(function(userData) {
								console.log(`Got back user data`);
								scores.update(userData);
							});
							if (!adding_res) {
								$('#roll-dice').removeClass('disabled').addClass('btn-floating blue');
								$('#add-cong').removeClass('disabled').addClass('btn-floating blue');
								$('#next-player').removeClass('disabled').addClass('btn-floating blue');
								if (userData.sel_tour == '3') {
									$('#add-elder').removeClass('disabled').addClass('btn-floating blue');
								} else {
									$('#add-believer').removeClass('disabled').addClass('btn-floating blue');
								}
								realtime.stop();
							}
						}
					} else {
						if (realtimeMarkers.hasOwnProperty(geopts[idx].properties.id)) {
							console.log(`${realtimeMarkers[geopts[idx].properties.id]._latlng.lng}, ${realtimeMarkers[geopts[idx].properties.id]._latlng.lat} AND ${geopts[idx].geometry.coordinates[0]}, ${geopts[idx].geometry.coordinates[1]}`);
							if (`${realtimeMarkers[geopts[idx].properties.id]._latlng.lng}, ${realtimeMarkers[geopts[idx].properties.id]._latlng.lat}` != `${geopts[idx].geometry.coordinates[0]}, ${geopts[idx].geometry.coordinates[1]}`) {
								map.removeLayer(realtimeMarkers[geopts[idx].properties.id]);
								var icon = L.icon({iconUrl: colouriseSVG(playerMarker, tourColours[geopts[idx].properties.sel_tour].player), iconSize: [48, 48]});
								realtimeMarkers[geopts[idx].properties.id] = L.marker([geopts[idx].geometry.coordinates[1], geopts[idx].geometry.coordinates[0]], {title: geopts[idx].properties.username, icon: icon, pane: 'playerMarkers'}).addTo(map);
								realtimeMarkers[geopts[idx].properties.id].bindTooltip(geopts[idx].properties.username, {'permanent': true, 'pane': 'tooltips'});
							}
						} else {
							var icon = L.icon({iconUrl: colouriseSVG(playerMarker, tourColours[geopts[idx].properties.sel_tour].player), iconSize: [48, 48]});
							realtimeMarkers[geopts[idx].properties.id] = L.marker([geopts[idx].geometry.coordinates[1], geopts[idx].geometry.coordinates[0]], {title: geopts[idx].properties.username, icon: icon, pane: 'playerMarkers'}).addTo(map);
							realtimeMarkers[geopts[idx].properties.id].bindTooltip(geopts[idx].properties.username, {'permanent': true, 'pane': 'tooltips'});
						}
					}
				} else {
					if (geopts[idx].properties.name.indexOf('Believer') > -1) {
						var icon = L.icon({iconUrl: colouriseSVG(believerSVG, tourColours[geopts[idx].properties.sel_tour].resource), iconSize: [36, 36]});
						realtimeMarkers[geopts[idx].properties.id] = L.marker([geopts[idx].geometry.coordinates[1], geopts[idx].geometry.coordinates[0]], {title: geopts[idx].properties.name, icon: icon, pane: 'resMarkers'}).addTo(map);
						realtimeMarkers[geopts[idx].properties.id].bindPopup(`<div>${geopts[idx].properties.name}</div>`, {'pane': 'popups'});
					} else if (geopts[idx].properties.name.indexOf('Elder') > -1) {
						var icon = L.icon({iconUrl: colouriseSVG(elderSVG, tourColours[geopts[idx].properties.sel_tour].resource), iconSize: [36, 36]});
						realtimeMarkers[geopts[idx].properties.id] = L.marker([geopts[idx].geometry.coordinates[1], geopts[idx].geometry.coordinates[0]], {title: geopts[idx].properties.name, icon: icon, pane: 'resMarkers'}).addTo(map);
						realtimeMarkers[geopts[idx].properties.id].bindPopup(`<div>${geopts[idx].properties.name}</div>`, {'pane': 'popups'});
					} else if (geopts[idx].properties.name.indexOf('Congregation') > -1) {
						var icon = L.icon({iconUrl: colouriseSVG(congSVG, tourColours[geopts[idx].properties.sel_tour].resource), iconSize: [36, 36]});
						realtimeMarkers[geopts[idx].properties.id] = L.marker([geopts[idx].geometry.coordinates[1], geopts[idx].geometry.coordinates[0]], {title: geopts[idx].properties.name, icon: icon, pane: 'resMarkers'}).addTo(map);
						realtimeMarkers[geopts[idx].properties.id].bindPopup(`<div>${geopts[idx].properties.name}</div>`, {'pane': 'popups'});
					}
				}
			}
		});
	}
}