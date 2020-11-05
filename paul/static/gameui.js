var placeIdx;
var cardData;

function addResource(e) {
	e.preventDefault();
	if ($(this).hasClass('disabled')) {
		return
	} else {
		$('#add-believer').removeClass('btn-floating blue').addClass('disabled');
		$('#add-cong').removeClass('btn-floating blue').addClass('disabled');
		$('#add-elder').removeClass('btn-floating blue').addClass('disabled');
	}
	console.log(`Entered ${e.currentTarget.title}`);
	$.when(
		$.getJSON(`/user/add-resource?userId=${$('#userId').val()}&r=${e.currentTarget.title.match(/\b(\w)/g)[1].toLowerCase()}`)
	).done(function(resourceRes) {
		console.log('Got back add resource res', resourceRes);
		if (resourceRes.alldone) {
			$('.modal-content h4').html(`${e.currentTarget.title}`);
			$('.modal-content p').html(`You've already added ${e.currentTarget.title.split(/\s/)[1].toLowerCase()}(s) to all required locations`);
			$('#submit-button').html('OK');
			var instance = M.Modal.getInstance($('.modal').modal());
			instance.open();
		} else if (resourceRes.msg) {
			$('.modal-content h4').html(`${e.currentTarget.title}`);
			$('.modal-content p').html(resourceRes.msg);
			$('#submit-button').html('OK');
			var instance = M.Modal.getInstance($('.modal').modal());
			instance.open();
		} else {
			$('.modal-content h4').html(`${e.currentTarget.title}`);
			$('.modal-content p').html(`Select a location to add the ${e.currentTarget.title.split(/\s/)[1].toLowerCase()}${resourceRes.resourcefield}`);
			$('#submit-button').html('SUBMIT');
			if (!$('#cancel', $('.modal-footer')).length) {
				$('<a href="#!" id="cancel" class="modal-close waves-effect waves-red btn-flat">Cancel</a>').insertBefore($('#submit-button'));
			}
			if (detectMobile()) {
				$('select').addClass('browser-default');
			}
			$('select').formSelect();
			var instance = M.Modal.getInstance($('.modal').modal({
				dismissible: false,
				onCloseEnd: function() {
					console.log(`Entered ${e.currentTarget.title} onCloseEnd function`);
					$('#cancel', $('.modal-footer')).remove();
					if ($('#location').val()) {
						$.when(
							$.getJSON(`/user/add-resource?userId=${$('#userId').val()}&r=${e.currentTarget.title.match(/\b(\w)/g)[1].toLowerCase()}&l=${$('#location').val()}`)
						).done(function(resourceRes) {
							console.log(`Got back final resourceRes`);
							M.toast({html: resourceRes.msg});
							if (resourceRes.updated) {
								fetch(`/get-game-state?userId=${$('#userId').val()}`)
								.then(function(response) {
									return response.json();
								})
								.then(function(response) {
									processGameState(response, true);
								})
								.then(function(response) {return fetch(`/user/get-user-data?userId=${$('#userId').val()}`);})
								.then(function(response) {
									console.log(`Got back user data`);
									return response.json();
								})
								.then(function(userData) {scores.update(userData);})
								.catch(function(error) {
									console.log('Request failed', error);
								});
							}
						})
					}
				}
			}));
			instance.open();
		}
	});
}

$(document).ready(function() {
	$('.fixed-action-btn').floatingActionButton({'direction': 'left'});
	$('#roll-dice').removeClass('btn-floating blue').addClass('disabled');
	$('#add-believer').removeClass('btn-floating blue').addClass('disabled');
	$('#add-cong').removeClass('btn-floating blue').addClass('disabled');
	$('#add-elder').removeClass('btn-floating blue').addClass('disabled');
	$('#next-player').removeClass('btn-floating blue').addClass('disabled');
	init();
	$('#roll-dice').on('click', function(e) {
		e.preventDefault();
		if ($(this).hasClass('disabled')) {
			return
		}
		$('.preloader-wrapper').show();
		$('#roll-dice').removeClass('btn-floating blue').addClass('disabled');
		const element = document.getElementById('dice-box');
		element.style.display = 'block';
		const options = {
			element,
			numberOfDice: 1, 
			callback: updateCurPos
		}
		rollADie(options);
	});
	$('#my-mission').on('click', function(e) {
		e.preventDefault();
		$.when(
			$.getJSON(`/user/get-rules?userId=${$('#userId').val()}`)
		).done(function(getRulesRes) {
			$('.modal-content h4').html(`Mission ${getRulesRes.mission}`);
			$('.modal-content p').html(getRulesRes.msg);
			$('#submit-button').html('OK');
			var instance = M.Modal.getInstance($('.modal').modal());
			instance.open();
		});
	});
	$('#rules').on('click', function(e) {
		e.preventDefault();
		$.when(
			$.getJSON(`/user/get-rules`)
		).done(function(getRulesRes) {
			$('.modal-content h4').html(`${e.currentTarget.title}`);
			var rules = $(getRulesRes.msg).addClass('browser-default');
			$('.modal-content p').html(rules);
			$('#submit-button').html('OK');
			var instance = M.Modal.getInstance($('.modal').modal());
			instance.open();
		});
	});
	$('#next-player').on('click', function(e) {
		e.preventDefault();
		if ($(this).hasClass('disabled')) {
			return
		}
		console.log(`Entered ${e.currentTarget.title}`);
		$.when(
			$.getJSON(`/user/next-user-turn?userId=${$('#userId').val()}`)
		).done(function(nextUserRes) {
			console.log('Got back next user res', nextUserRes);
			$('#roll-dice').removeClass('btn-floating blue').addClass('disabled');
			$('#add-believer').removeClass('btn-floating blue').addClass('disabled');
			$('#add-cong').removeClass('btn-floating blue').addClass('disabled');
			$('#next-player').removeClass('btn-floating blue').addClass('disabled');
			$('#add-elder').removeClass('btn-floating blue').addClass('disabled');
			if (nextUserRes.won) {
				$('.modal-content h4').html(`Game Over`);
				$('.modal-content p').html(nextUserRes.msg);
				$('#submit-button').html('OK');
				var instance = M.Modal.getInstance($('.modal').modal());
				instance.open();
			} else {
				M.toast({html: nextUserRes.msg});
				$.when(
					$.getJSON(`/user/get-user-data?userId=${$('#userId').val()}`)
				).done(function(userData) {
					console.log(`Got back user data`);
					scores.update(userData);
				});
				realtime.start();
			}
		})
	});
	$('#add-believer').on('click', addResource);
	$('#add-elder').on('click', addResource);
	$('#add-cong').on('click', addResource);
});

function updateCurPos(diceVal) {
	console.log(`Entered updateCurPos ${diceVal}`);
	$.when(
		$.getJSON(`/user/get-user-data?userId=${$('#userId').val()}`),
		$.getJSON('/static/tours.json')
	).done(function(userDataRes, toursRes) {
		userData = userDataRes[0];
		var tours = toursRes[0];
		map.removeLayer(curLocMarker);
		if (!placeIdx) {
			placeIdx = userData.curpos;
		}
		if (placeIdx + diceVal[0] < tours[userData.sel_tour].length) {
			placeIdx = placeIdx + diceVal[0];
			console.log(`Dice less than place length: ${tours[userData.sel_tour][placeIdx].lat}`);
			var icon = L.icon({iconUrl: colouriseSVG(playerMarker, tourColours[userData.sel_tour].player), iconSize: [48, 48]});
			curLocMarker = L.marker([tours[userData.sel_tour][placeIdx].lat, tours[userData.sel_tour][placeIdx].lng], {title: userData.username, icon: icon, pane: 'playerMarkers'}).addTo(map);
			curLocMarker.bindTooltip(userData.username, {'permanent': true, 'pane': 'tooltips'});
		} else {
			placeIdx = (placeIdx + diceVal[0]) - (tours[userData.sel_tour].length - 1);
			console.log(`Dice val more than place length: ${tours[userData.sel_tour][placeIdx].lat}`);
			var icon = L.icon({iconUrl: colouriseSVG(playerMarker, tourColours[userData.sel_tour].player), iconSize: [48, 48]});
			curLocMarker = L.marker([tours[userData.sel_tour][placeIdx].lat, tours[userData.sel_tour][placeIdx].lng], {title: userData.username, icon: icon, pane: 'playerMarkers'}).addTo(map);
			curLocMarker.bindTooltip(userData.username, {'permanent': true, 'pane': 'tooltips'});
		}
		$.when(
			$.getJSON(`/user/update-curpos?placeIdx=${placeIdx}&userId=${$('#userId').val()}`),
			$.getJSON(`/card/get-card?location=${tours[userData.sel_tour][placeIdx].name}&tour=${userData.sel_tour}&userId=${$('#userId').val()}`)
		).done(function(curPosRes, cardDataRes) {
			console.log(curPosRes[0].msg);
			if (curPosRes[0].msg.search('You gained') > -1) {
				M.toast({html: curPosRes[0].msg});
			}
			console.log('got back card data', cardDataRes[0]);
			if (cardDataRes[0].score != null) {
				cardData = cardDataRes[0];
				var content;
				if (cardData.content.toLowerCase().startsWith('bonus:')) {
					$('.modal-content h4').html('Bonus Quiz Card');
					content = cardData.content.slice(6);
				} else {
					$('.modal-content h4').html('Card');
					content = cardData.content;
				}
				if (['Sea Trial', 'Land Trial', 'City Trial'].includes(cardData.type)) {
					$('.modal-content p').html(`${content}<br />${cardData.result}`);
					$('#submit-button').html('OK');
				} else {
					$('.modal-content p').html(content);
					$('#submit-button').html('SUBMIT');
				}
				if (detectMobile()) {
					$('select').addClass('browser-default');
				}
				$('select').formSelect();
				var instance = M.Modal.getInstance(
					$('.modal').modal({
						dismissible: false,
						onCloseEnd: function() {
							console.log('Entered onCloseEnd function');
							if (cardData.result) {
								if (['City Quiz', 'Quiz'].includes(cardData.type)) {
									if ($('#answer').val()) {
										if ($('#answer').val().toLowerCase() == cardData.result.toLowerCase()) {
											console.log('Got correct answer', $('#answer').val());
											$.when(
												$.getJSON(`/card/handle-right-answer?cardscore=${JSON.stringify(cardData.score)}&userId=${$('#userId').val()}&cardId=${cardData.id}`)
											).done(function(rightAnswerRes) {
												console.log('Got back right answer response');
												scores.update(rightAnswerRes);
												$('.modal-content p').html(`You answered correctly!`);
												$('#submit-button').html('OK');
												instance.open();
											});
										} else {
											console.log('Got incorrect answer', $('#answer').val());
											$.when(
												$.getJSON(`/card/handle-wrong-answer?userId=${$('#userId').val()}&cardId=${cardData.id}`)
											).done(function(wrongAnswerRes) {
												console.log(wrongAnswerRes.msg);
												var result;
												if (cardData.more_info) {
													var moreinfo = cardData.more_info.replace(/<[\/]{0,1}(p)[^><]*>/ig,"");
													result = `${cardData.result}<br />${$(moreinfo).attr('target', '_blank').prop('outerHTML')}`;
												} else {
													result = cardData.result;
												}
												$('.modal-content p').html(`You answered incorrectly. The answer was:<br />${result}`);
												$('#submit-button').html('OK');
												instance.open();
											});
										}
									}
								} else {
									if (cardData.curpos != null) {
										map.removeLayer(curLocMarker);
										var icon = L.icon({iconUrl: colouriseSVG(playerMarker, tourColours[userData.sel_tour].player), iconSize: [48, 48]});
										curLocMarker = L.marker([tours[userData.sel_tour][cardData.curpos].lat, tours[userData.sel_tour][cardData.curpos].lng], {title: userData.username, icon: icon, pane: 'playerMarkers'}).addTo(map);
										curLocMarker.bindTooltip(userData.username, {'permanent': true, 'pane': 'tooltips'});
									} else {
										var resources = ['b', 'c', 'e', 's', 'f', 'p'];
										var cardScores = resources.filter(resource => Object.keys(cardData.score).includes(resource));
										console.log('Filtered card scores', cardScores);
										if (cardScores.length > 0) {
											$.when(
												$.getJSON(`/user/get-user-data?userId=${$('#userId').val()}`)
											).done(function(userData) {
												console.log(`Got back user scores data`);
												scores.update(userData);
											});
										}
									}
								}
							}
						}
					})
				);
				$('.preloader-wrapper').hide();
				instance.open();
			} else {
				$('.preloader-wrapper').hide();
				console.log('No card returned');
			}
		});
	});
}