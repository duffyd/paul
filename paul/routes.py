import copy
import csv
from datetime import datetime
from io import StringIO
import json
import logging
import os
from flask import flash, jsonify, redirect, render_template, request, url_for, abort
from flask_login import current_user, login_user, logout_user, login_required
from markdown import markdown
import random
from shapely.geometry import Point, mapping
from sqlalchemy import extract
from sys import stdout
import urllib.parse
from werkzeug.urls import url_parse
from paul import app
from paul import db
from paul.forms import LoginForm, RegistrationForm, UserForm, CardForm
from paul.models import User, Card, UserTurn
from paul.config import INITIAL_SCORE, MISSIONS, B_PLACES, C_PLACES, E_PLACES, \
    RULES, MISSIONS_TEXT

logger = logging.getLogger()
logging.basicConfig(stream=stdout, level=logging.DEBUG, format="%(asctime)s %(message)s",
                    datefmt="%m/%d/%Y %I:%M:%S %p")

tours = json.load(open(os.path.join(os.path.dirname(__file__), 'static', 'tours.json'), 'r'))

@app.route("/")
@login_required
def index():
    game_id = request.args.get('g', None)
    if not game_id:
        return redirect(url_for('login'))
    return render_template(
        'index.html',
        game_id=game_id
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    adminuser = os.environ.get('ADMIN_USER', None)
    if current_user.is_authenticated:
        if current_user.username != adminuser:
            return redirect('{}?g={}'.format(url_for('index'), current_user.created_at.toordinal()))
        else:
            return redirect(url_for('list_users'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        if current_user.username != adminuser:
            next_page = url_for('index')
            return redirect('{}?g={}'.format(next_page, user.created_at.toordinal()))
        else:
            return redirect(url_for('list_users'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    adminuser = os.environ.get('ADMIN_USER', None)
    if current_user.is_authenticated:
        if current_user.username != adminuser:
            return redirect('{}?g={}'.format(url_for('index'), current_user.created_at.toordinal()))
        else:
            return redirect(url_for('list_users'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if form.username.data != adminuser:
            now = datetime.now()
            users = User.query.filter(
                extract('month', User.created_at) == now.month,
                extract('year', User.created_at) == now.year,
                extract('day', User.created_at) == now.day
            ).all()
            if len(users) >= 3:
                flash('Apologies but a maximum of 3 users can register to play this game')
                return redirect(url_for('login'))
            for player in users:
                if player.sel_tour == form.sel_tour.data:
                    flash('Another player has already selected that missionary tour. Please select another one')
                    return redirect(url_for('register'))
        user = User(
            username=form.username.data,
            email=form.email.data,
            sel_tour=form.sel_tour.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        if form.username.data != adminuser:
            userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
            if not userturn:
                players = User.query.filter(
                    extract('month', User.created_at) == user.created_at.month,
                    extract('year', User.created_at) == user.created_at.year,
                    extract('day', User.created_at) == user.created_at.day
                ).order_by(User.id).all()
                userturn = UserTurn(
                    game_id=str(user.created_at.toordinal()),
                    user=players[0]
                )
                db.session.add(userturn)
                db.session.commit()
                logger.info('Successfully created userturn for %s', user.username)
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

def collate_player_data(user):
    players = User.query.filter(
        extract('month', User.created_at) == user.created_at.month,
        extract('year', User.created_at) == user.created_at.year,
        extract('day', User.created_at) == user.created_at.day
    ).all()
    userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
    player_data = {}
    for player in players:
        if player.username != user.username:
            player_data[player.username] = dict(
                mission=MISSIONS[player.sel_tour],
                score=eval(player.score),
                sel_tour=player.sel_tour,
                game_over=player.id in eval(userturn.game_over) and True or False
            )
    return player_data

@app.route('/user/get-user-data', methods=['GET'])
def get_user_data():
    userid = request.args.get('userId')
    user = User.query.filter_by(id=int(userid)).first_or_404()
    player_data = collate_player_data(user)
    userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
    return jsonify({
        'username': user.username,
        'curpos': user.curpos,
        'sel_tour': user.sel_tour,
        'score': eval(user.score),
        'mission_done': user.sel_tour == '3' and {'c': sum(eval(user.c_places).values()), 'e': sum(eval(user.e_places).values()), 's': eval(user.score)['s']} or {'b': sum(eval(user.b_places).values()), 'c': sum(eval(user.c_places).values()), 's': eval(user.score)['s']},
        'mission': MISSIONS[user.sel_tour],
        'player_data': player_data,
        'userturn': userturn.user and userturn.user.username or None
    }), 200

@app.route('/user/get-rules', methods=['GET'])
def get_rules():
    userid = request.args.get('userId', None)
    if userid:
        user = User.query.filter_by(id=int(userid)).first_or_404()
        return jsonify({'msg': markdown(MISSIONS_TEXT[user.sel_tour], extensions=['sane_lists']), 'mission': user.sel_tour}), 200
    else:
        return jsonify({'msg': markdown(RULES, extensions=['sane_lists'])}), 200
    
@app.route('/user/update-curpos', methods=['GET'])
def update_curpos():
    place_idx = int(request.args.get('placeIdx'))
    user = User.query.filter_by(id=int(request.args.get('userId'))).first_or_404()
    userscore = eval(user.score)
    msg = 'Successfully updated curpos for {}'.format(user.username)
    updated = False
    if user.curpos > place_idx:
        userscore['f'] += 1
        userscore['s'] += 1
        userscore['t'] += 1
        updated = True
    if user.sel_tour == '1':
        if place_idx == 7:
            userscore['f'] += 1
            userscore['s'] += 1
            msg = "You gained 1x food & 1x money due to landing on Paphos"
            updated = True
    else:
        if place_idx == 1:
            userscore['f'] += 1
            userscore['s'] += 1
            msg = "You gained 1x food & 1x money due to landing on Tarsus"
            updated = True
    if updated:
        user.score = str(userscore)
        logger.info('Successfully updated score for %s', user.username)
    user.curpos = place_idx
    db.session.commit()
    logger.info(msg)
    return jsonify({'msg': msg}), 200

def index(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1

def pay_for_res(resource, score, updated):
    if resource == 'b' and score[resource] > 0:
        score[resource] -= 1
        updated = True
    elif resource == 'e':
        if score['b'] >= 2:
            score['b'] -= 2
            updated = True
    elif resource == 'c':
        if score['b'] >= 3:
            score['b'] -= 3
            updated = True
    return score, updated

@app.route('/user/add-resource', methods=['GET'])
def add_resource():
    updated = False
    user = User.query.filter_by(id=int(request.args.get('userId'))).first_or_404()
    resource = request.args.get('r')
    if resource == 'b':
        tour_res_goals = B_PLACES[user.sel_tour]
        resname = 'believer'
    elif resource == 'c':
        tour_res_goals = C_PLACES[user.sel_tour]
        resname = 'congregation'
    elif resource == 'e':
        tour_res_goals = E_PLACES[user.sel_tour]
        resname = 'elder'
    tourcrcts = eval(user.score)['t']
    if tourcrcts == 0:
        return jsonify({'msg': 'You must complete 1 tour circuit before you can add a {}'.format(resname)}), 200
    loc = request.args.get('l', None)
    user_res_places = eval(getattr(user, '{}_places'.format(resource)))
    if not loc:
        menuitems = []
        alldone = True
        for place in tour_res_goals.keys():
            try:
                if user_res_places[place] < tour_res_goals[place]:
                    alldone = False
                    menuitems.append(place)
            except KeyError:
                alldone = False
                menuitems.append(place)
        if alldone is True:
            return jsonify({'alldone': alldone}), 200
        else:
            return jsonify({
                'resourcefield': '<select name="location" id="location"><option value="">Select location</option>{}</select>'.format(''.join(['<option value="{}">{}</option>'.format(item, item) for item in menuitems]))
            }), 200
    else:
        score = eval(user.score)
        try:
            if (user_res_places[loc]+1) <= tour_res_goals[loc]:
                score, updated = pay_for_res(resource, score, updated)
            elif (user_res_places[loc]+1) > tour_res_goals[loc]:
                return jsonify({'msg': "You've already reached the required number of {}s for this location. Please select another location".format(resname)}), 200
        except KeyError:
            score, updated = pay_for_res(resource, score, updated)
    if updated:
        try:
            user_res_places[loc] += 1
        except KeyError:
            user_res_places[loc] = 1
        user.score = str(score)
        setattr(user, '{}_places'.format(resource), str(user_res_places))
        db.session.commit()
        logger.info('Successfully added %s at %s for %s', resname, loc, user.username)
        return jsonify({'msg': 'Successfully added {} at {}'.format(resname, loc), 'updated': True}), 200
    return jsonify({'msg': "You don't have enough resources. Try again later"}), 200

@app.route('/user/next-user-turn', methods=['GET'])
def next_user_turn():
    user = User.query.filter_by(id=int(request.args.get('userId'))).first_or_404()
    userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
    completed = True
    for mission in MISSIONS[user.sel_tour].keys():
        if mission != 's':
            if sum(eval(getattr(user, '{}_places'.format(mission))).values()) < MISSIONS[user.sel_tour][mission]:
                completed = False
        elif eval(user.score)[mission] < MISSIONS[user.sel_tour][mission]:
            completed = False
    if completed:
        userturn.won = user.username
        db.session.commit()
        return jsonify({'msg': "{} has won 🏆!".format(userturn.won), 'won': True}), 200
    players = User.query.filter(
        extract('month', User.created_at) == user.created_at.month,
        extract('year', User.created_at) == user.created_at.year,
        extract('day', User.created_at) == user.created_at.day
    ).order_by(User.id).all()
    game_over = []
    for player in players:
        if eval(player.score)['f'] == 0 and eval(player.score)['s'] == 0:
            if player.id not in eval(userturn.game_over):
                game_over.append(player.id)
    if len(game_over) > 0:
        userturn.game_over = str(game_over)
    player_unames = [player.username for player in players]
    miss_turn = eval(userturn.miss_turn)
    idx = player_unames.index(user.username)
    while True:
        idx = (idx + 1) % len(player_unames)
        if players[idx].id in miss_turn:
            miss_turn.remove(players[idx].id)
        elif players[idx].id in eval(userturn.game_over):
            continue
        else:
            break
    if len(eval(userturn.miss_turn)) != len(miss_turn):
        userturn.miss_turn = str(miss_turn)
    userturn.user = players[idx]
    db.session.commit()
    return jsonify({'msg': "Thanks! Now it's {}'s turn".format(players[idx].username)}), 200
    
def add_card_score(cardscore, userscore, updated, user):
    for key in cardscore.keys():
        if key == 'm':
            userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
            miss_turn = eval(userturn.miss_turn)
            for i in range(cardscore[key]):
                miss_turn.append(user.id)
            userturn.miss_turn = str(miss_turn)
            db.session.commit()
            logger.info('Successfully updated miss_turn for %s', user.username)
        elif key == 'i':
            if user.curpos + cardscore[key] < 0:
                user.curpos = 0
            else:
                user.curpos += cardscore[key]
            updated = True
        elif key == 'p':
            players = User.query.filter(
                extract('month', User.created_at) == user.created_at.month,
                extract('year', User.created_at) == user.created_at.year,
                extract('day', User.created_at) == user.created_at.day
            ).all()
            for player in players:
                if player.username != user.username:
                    playerscore = eval(player.score)
                    resourcetotake = next(iter(cardscore[key]))
                    playerscore[resourcetotake] += cardscore[key][resourcetotake]
                    if playerscore[resourcetotake] < 0:
                        playerscore[resourcetotake] = 0
                    userscore[resourcetotake] += abs(cardscore[key][resourcetotake])
                    updated = True
                    player.score = str(playerscore)
                    db.session.commit()
                    logger.info('Successfully updated score for %s', player.username)
        else:
            if key == 'c' and len(eval(user.c_places).items()) > 0:
                cplaces = eval(user.c_places)
                cplaces[next(iter(cplaces))] += cardscore[key]
                if cplaces[next(iter(cplaces))] < 0:
                    del cplaces[next(iter(cplaces))]
                user.c_places = str(cplaces)
                updated = True
                logger.info('Successfully removed a cong for %s', user.username)
            userscore[key] += cardscore[key]
            if userscore[key] < 0:
                userscore[key] = 0
            updated = True
    return cardscore, userscore, updated, user

@app.route('/card/handle-right-answer', methods=['GET'])
def handle_right_answer():
    cardscore = json.loads(request.args.get('cardscore'))
    user = User.query.filter_by(id=int(request.args.get('userId'))).first_or_404()
    cardid = request.args.get('cardId')
    seen_cards = eval(user.seen_cards)
    userscore = eval(user.score)
    updated = False
    cardscore, userscore, updated, user = add_card_score(cardscore, userscore, updated, user)
    userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
    player_data = collate_player_data(user)
    if updated:
        seen_cards.append(int(cardid))
        user.seen_cards = str(seen_cards)
        user.score = str(userscore)
        db.session.commit()
        logger.info('Successfully updated score for %s', user.username)
    return jsonify({
        'username': user.username,
        'curpos': user.curpos,
        'sel_tour': user.sel_tour,
        'score': eval(user.score),
        'mission': MISSIONS[user.sel_tour],
        'mission_done': user.sel_tour == '3' and {'c': sum(eval(user.c_places).values()), 'e': sum(eval(user.e_places).values()), 's': eval(user.score)['s']} or {'b': sum(eval(user.b_places).values()), 'c': sum(eval(user.c_places).values()), 's': eval(user.score)['s']},
        'player_data': player_data,
        'userturn': userturn.user and userturn.user.username or None
    }), 200

@app.route('/card/handle-wrong-answer', methods=['GET'])
def handle_wrong_answer():
    msg = 'Successfully processed wrong answer'
    user = User.query.filter_by(id=int(request.args.get('userId'))).first_or_404()
    cardid = int(request.args.get('cardId'))
    seen_cards = eval(user.seen_cards)
    if not cardid in seen_cards:
        seen_cards.append(cardid)
        user.seen_cards = str(seen_cards)
        db.session.commit()
        msg = 'Successfully updated seen_cards for {}'.format(user.username)
    logger.info(msg)
    return jsonify({'msg': msg}), 200
    
@app.route('/card/get-card', methods=['GET'])
def get_card():
    start_time = datetime.now()
    card = None
    id = None
    type = None
    content = None
    result = None
    more_info = None
    cardscore = None
    curpos = None
    location = urllib.parse.unquote(request.args.get('location'))
    tour = request.args.get('tour')
    user = User.query.filter_by(id=int(request.args.get('userId'))).first_or_404()
    if location in ['Land Trial', 'Quiz', 'Sea Trial']:
        cards = Card.query.filter(Card.type.in_(('Land Trial', 'Quiz', 'Sea Trial'))).all()
    else:
        cards = Card.query.filter_by(location=location, tour=tour).all()
        if len(cards) == 0:
            cards = Card.query.filter(Card.type.in_(('Land Trial', 'Quiz'))).all()
    if len(cards) != 0:
        cardchoices = copy.deepcopy(cards)
        cardchoices.extend([None] * round(len(cards)/3))
        card = random.choice(cardchoices)
        if card:
            seen_cards = eval(user.seen_cards)
            processed = []
            idx = 0
            while True:
                if location not in ['Land Trial', 'Quiz', 'Sea Trial']:
                    # User is on a city
                    if idx == len(cards):
                        cards = Card.query.filter(Card.type.in_(('Land Trial', 'Quiz'))).all()
                        processed = []
                        card = random.choice(cards)
                    if card.type in ['Land Trial', 'Sea Trial']:
                        if seen_cards.count(card.id) <= 2:
                            break
                    if card.id in seen_cards:
                        processed.append(card.id)
                        card = random.choice(cards)
                    else:
                        break
                else:
                    if card.type == 'Quiz':
                        if card.id in seen_cards:
                            processed.append(card.id)
                            card = random.choice(cards)
                        else:
                            break
                    else:
                        if seen_cards.count(card.id) <= 2:
                            break
                        else:
                            processed.append(card.id)
                            card = random.choice(cards)
                if len(list(set(processed))) == len(cards):
                    card = None
                    break
                idx += 1
            if card:
                id = card.id
                type = card.type
                content = card.content
                result = card.result
                more_info = card.more_info and markdown(card.more_info) or None
                cardscore = eval(card.score)
                userscore = eval(user.score)
                updated = False
                if card.type in ['Land Trial', 'Sea Trial']:
                    cardscore, userscore, updated, user = add_card_score(cardscore, userscore, updated, user)
                elif card.type == 'City Trial':
                    if card.id not in seen_cards:
                        cardscore, userscore, updated, user = add_card_score(cardscore, userscore, updated, user)
                if updated:
                    if 'i' in cardscore.keys():
                        curpos = user.curpos
                    seen_cards.append(card.id)
                    user.seen_cards = str(seen_cards)
                    user.score = str(userscore)
                    db.session.commit()
                    logger.info('Successfully updated score for %s', user.username)
    logger.info("Got card in {}".format(datetime.now() - start_time))
    return jsonify({
        'id': id,
        'type': type,
        'content': content,
        'result': result,
        'more_info': more_info,
        'score': cardscore,
        'curpos': curpos
    }), 200

@app.errorhandler(403)
def custom_403(error):
    return render_template('403.html'), 403

@app.route("/upload-csv", methods=['GET', 'POST'])
@login_required
def upload_csv():
    adminuser = os.environ.get('ADMIN_USER', None)
    if adminuser:
        if current_user.username != adminuser:
            abort(403)
    else:
        abort(403)
    filereader = []
    msg = ''
    
    if request.method == 'POST':
        numimported = 0
        numupdated = 0
        csvfile = request.files['csvfile']
        filereader = csv.reader(StringIO(csvfile.read().decode("UTF-8")))
        if request.form['upload_type'] == 'cards':
            if request.form['dont_delete_card'] != 'true':
                num_rows_deleted = db.session.query(Card).delete()
                db.session.commit()
                logger.info('Successfully deleted %d card(s)', num_rows_deleted)
            for i, row in enumerate(filereader):
                    if i >= 1:
                        cardexists = Card.query.filter_by(content=row[2]).first()
                        if not cardexists:
                            try:
                                card = Card(
                                    location=row[0],
                                    type=row[1],
                                    content=row[2],
                                    result=row[3],
                                    more_info=row[4],
                                    tour=row[5],
                                    score=row[6]
                                )
                                db.session.add(card)
                                db.session.commit()
                                numimported += 1
                            except:
                                import pdb;pdb.set_trace()
            if numimported > 0:
                msg = 'Successfully imported {} card(s)'.format(numimported)
                
        if msg != '':
            logger.info(msg)
            flash(msg, 'success')
        
    return render_template(
        'uploadcsv.html',
        title='Upload CSV'
    )

@app.route('/card/list-cards', methods=('GET', 'POST'))
@login_required
def list_cards():
    adminuser = os.environ.get('ADMIN_USER', None)
    if adminuser:
        if current_user.username != adminuser:
            abort(403)
    else:
        abort(403)
    return render_template(
        'list-cards.html',
        cards=Card.query.order_by(Card.tour, Card.type).all(),
        title="List Cards"
    )
    
@app.route('/user/list-users', methods=('GET', 'POST'))
@login_required
def list_users():
    adminuser = os.environ.get('ADMIN_USER', None)
    if adminuser:
        if current_user.username != adminuser:
            abort(403)
    else:
        abort(403)
    return render_template(
        'list-users.html',
        users=User.query.order_by(User.username).all(),
        title="List Users"
    )

@app.route('/del-item', methods=['POST'])
def del_item():
    req_json = request.get_json()
    itemid = req_json['itemid']
    itemtype = req_json['itemtype']
    if itemtype == 'card':
        item = Card.query.filter_by(id=eval(itemid))
    elif itemtype == 'user':
        item = User.query.filter_by(id=eval(itemid))
    if item:
        obj = item.first()
        try:
            itemname = getattr(obj, 'username')
        except AttributeError:
            itemname = getattr(obj, 'location')
        if itemtype == 'user':
            users = User.query.filter_by(id=int(itemid)).all()
            if len(users) == 1:
                userturn = UserTurn.query.filter_by(game_id=str(users[0].created_at.toordinal()))
                userturn.delete()
                logger.info('Successfully deleted userturn for %s', users[0].username)
        item.delete()
        db.session.commit()
        msg = "Successfully deleted {:s}".format(itemname)
    else:
        msg = "Could not find {:s}".format(itemtype)
    return {"msg": msg}

@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    adminuser = os.environ.get('ADMIN_USER', None)
    if adminuser:
        if current_user.username != adminuser:
            abort(403)
    else:
        abort(403)
    user = User.query.filter_by(id=user_id).first()
    form = UserForm(obj=user)
    if request.method == 'POST' and form.validate():
        form.populate_obj(user)
        db.session.commit()
        flash('User saved')
    return render_template(
        'item.html',
        form=form,
        title='Edit User'
    )

@app.route('/card/edit/<int:card_id>', methods=['GET', 'POST'])
@login_required
def card_edit(card_id):
    adminuser = os.environ.get('ADMIN_USER', None)
    if adminuser:
        if current_user.username != adminuser:
            abort(403)
    else:
        abort(403)
    card = Card.query.filter_by(id=card_id).first()
    form = CardForm(obj=card)
    if form.validate_on_submit():
        if form.type.data in ['', None]:
            flash('You must select a card type')
        else:
            form.populate_obj(card)
            db.session.commit()
            flash('Card saved')
    return render_template(
        'item.html',
        form=form,
        title='Edit Card'
    )

@app.route('/card/add', methods=('GET', 'POST'))
@login_required
def card_add():
    adminuser = os.environ.get('ADMIN_USER', None)
    if adminuser:
        if current_user.username != adminuser:
            abort(403)
    else:
        abort(403)
    form = CardForm()
    if form.validate_on_submit():
        if form.type.data in ['', None]:
            flash('You must select a card type')
        else:
            newcard = Card(
                tour=form.tour.data,
                location=form.location.data,
                type=form.type.data,
                content=form.content.data,
                result=form.result.data,
                more_info=form.more_info.data,
                score=form.score.data,
            )
            db.session.add(newcard)
            db.session.commit()
            flash('{:s} card has been created'.format(form.type.data), 'success')
            return redirect(url_for("card_edit", card_id=newcard.id))
    return render_template(
        'item.html',
        form=form,
        title="Add Card"
    )

@app.route('/get-game-state', methods=['GET', 'POST'])
def get_game_state():
    won = False
    msg = ''
    user = User.query.filter_by(id=int(request.args.get('userId'))).first_or_404()
    userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
    if hasattr(userturn, 'won') and getattr(userturn, 'won') not in ['', None]:
        msg = "{} has won 🏆!".format(userturn.won)
        won = True 
    players = User.query.filter(
        extract('month', User.created_at) == user.created_at.month,
        extract('year', User.created_at) == user.created_at.year,
        extract('day', User.created_at) == user.created_at.day
    ).order_by(User.id).all()
    geopts = []
    for player in players:
        geopts.append({'type': 'Feature', 'properties': {'id': str(player.id), 'sel_tour': player.sel_tour, 'userturn': str(userturn.user.id), 'username': player.username}, 'geometry': mapping(Point(tours[player.sel_tour][player.curpos]['lng'], tours[player.sel_tour][player.curpos]['lat']))})
        if player.sel_tour == '3':
            resources = [dict(name='Believer', attrib='b_places'), dict(name='Elder', attrib='e_places'), dict(name='Congregation', attrib='c_places')]
        else:
            resources = [dict(name='Believer', attrib='b_places'), dict(name='Congregation', attrib='c_places')]
        for resource in resources:
            user_res = eval(getattr(player, resource['attrib']))
            for place in user_res.keys():
                place_data = next((item for item in tours[player.sel_tour] if item["name"] == place), None)
                geopts.append({'type': 'Feature', 'properties': {'id': "{}{}".format(str(player.id), place), 'sel_tour': player.sel_tour, 'name': "{}{} ({})".format(resource['name'], user_res[place] > 1 and 's' or '', user_res[place])}, 'geometry': mapping(Point(place_data['lng'], place_data['lat']))})
    return jsonify({'geopts': geopts, 'won': won, 'msg': msg}), 200

@app.route('/fixup', methods=['GET', 'POST'])
@login_required
def fixup():
    adminuser = os.environ.get('ADMIN_USER', None)
    if adminuser:
        if current_user.username != adminuser:
            abort(403)
    else:
        abort(403)
    user = User.query.filter_by(username='duffyd').first_or_404()
    userturn = UserTurn.query.filter_by(game_id=str(user.created_at.toordinal())).first()
    userturn.won = ''
    db.session.commit()
    logger.info('Updated userturn for %s', user.username)
    return redirect(url_for('list_users'))