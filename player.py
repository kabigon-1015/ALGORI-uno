#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import math
import os
import random
import sys
import time

import socketio

from rich import print


class SocketConst:
    class EMIT:
        JOIN_ROOM = 'join-room'
        RECEIVER_CARD = 'receiver-card'
        FIRST_PLAYER = 'first-player'
        COLOR_OF_WILD = 'color-of-wild'
        UPDATE_COLOR = 'update-color'
        SHUFFLE_WILD = 'shuffle-wild'
        NEXT_PLAYER = 'next-player'
        PLAY_CARD = 'play-card'
        DRAW_CARD = 'draw-card'
        PLAY_DRAW_CARD = 'play-draw-card'
        CHALLENGE = 'challenge'
        PUBLIC_CARD = 'public-card'
        SAY_UNO_AND_PLAY_CARD = 'say-uno-and-play-card'
        SAY_UNO_AND_PLAY_DRAW_CARD = 'say-uno-and-play-draw-card'
        POINTED_NOT_SAY_UNO = 'pointed-not-say-uno'
        SPECIAL_LOGIC = 'special-logic'
        FINISH_TURN = 'finish-turn'
        FINISH_GAME = 'finish-game'
        PENALTY = 'penalty'


class Special:
    SKIP = 'skip'
    REVERSE = 'reverse'
    DRAW_2 = 'draw_2'
    WILD = 'wild'
    WILD_DRAW_4 = 'wild_draw_4'
    WILD_SHUFFLE = 'wild_shuffle'
    WHITE_WILD = 'white_wild'


class Color:
    RED = 'red'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    BLACK = 'black'
    WHITE = 'white'


class DrawReason:
    DRAW_2 = 'draw_2'
    WILD_DRAW_4 = 'wild_draw_4'
    BIND_2 = 'bind_2'
    NOTING = 'nothing'


SPECIAL_LOGIC_TITLE = '○○○○○○○○○○○○○○○○○○○○○○○○○○○○'
ARR_COLOR = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]
ARR_COLOR_KANJI={Color.RED:'赤色',Color.YELLOW:'黄色',Color.GREEN:'緑色',Color.BLUE:'青色'}
TEST_TOOL_HOST_PORT = '3000'
TIME_DELAY = 10


print('Start demo player ...')

parser = argparse.ArgumentParser(description='A demo player written in Python')
parser.add_argument('host', action='store', type=str,
                    help='Host to connect')
parser.add_argument('room_name', action='store', type=str,
                    help='Name of the room to join')
parser.add_argument('player', action='store', type=str,
                    help='Player name you join the game as')
parser.add_argument('event_name', action='store', nargs='?', default=None, type=str,
                    help='Event name for test tool')

args = parser.parse_args(sys.argv[1:])
host = args.host
room_name = args.room_name
player = args.player
event_name = args.event_name
is_test_tool = TEST_TOOL_HOST_PORT in host

print('Start demo player ...')

print({
    'host': host,
    'room_name': room_name,
    'player': player,
    'is_test_tool': is_test_tool,
    'event_name': event_name
})

TEST_TOOL_EVENT_DATA = {
    'join-room': {
        'player': player,
        'room_name': room_name,
    },
    'play-card': {
        'card_play': {
            'color': 'red',
            'number': 6
        },
    },
    'color-of-wild': {
        'color_of_wild': 'red',
    },
    'draw-card': {},
    'play-draw-card': {
        'is_play_card': True,
    },
    'say-uno-and-play-card': {
        'card_play': {
            'color': 'red',
            'number': 6
        },
    },
    'say-uno-and-play-draw-card': {},
    'pointed-not-say-uno': {
        'target': 'Player 1',
    },
    'challenge': {
        'is_challenge': True,
    },
    'special-logic': {
        'title': SPECIAL_LOGIC_TITLE,
    },
}


once_connected = False

id = ''
cards_global = []
uno_declared = {}

color_check={}
draw_id=''
is_wild_sabotage=False
next_id=''
left_id=''
right_id=''
current_card={}

if not host:
    print('Host missed')
    os._exit(0)

if not room_name or not player:
    print('Arguments invalid')
    # If test-tool, ignore exit

    if not is_test_tool:
        os._exit(0)

# SocketIO Client
# sio = socketio.Client(engineio_logger=True, logger=True)
sio = socketio.Client()

# 共通エラー処理


def handle_error(event, err):
    if not err:
        return

    print('{} event failed!'.format(event))
    print(err)


# イベント送信
def send_join_room(data, callback):
    sio.emit(
        SocketConst.EMIT.JOIN_ROOM,
        data,
        callback=callback
    )


def send_color_of_wild(data):
    print('{} data_req:'.format(SocketConst.EMIT.COLOR_OF_WILD), data)
    sio.emit(
        SocketConst.EMIT.COLOR_OF_WILD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.COLOR_OF_WILD, err)
    )


def send_play_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.PLAY_CARD), data)
    sio.emit(
        SocketConst.EMIT.PLAY_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.PLAY_CARD, err)
    )


def send_draw_card(data):
    global draw_id
    draw_id=''
    print('{} data_req:'.format(SocketConst.EMIT.DRAW_CARD), data)
    sio.emit(
        SocketConst.EMIT.DRAW_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.DRAW_CARD, err)
    )


def send_play_draw_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), data)
    sio.emit(
        SocketConst.EMIT.PLAY_DRAW_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.PLAY_DRAW_CARD, err)
    )


def send_say_uno_and_play_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD), data)
    sio.emit(
        SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD, err)
    )


def send_say_uno_and_play_draw_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD), data)
    sio.emit(
        SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD, err)
    )


def send_pointed_not_say_uno(data):
    print('{} data_req:'.format(SocketConst.EMIT.POINTED_NOT_SAY_UNO), data)
    sio.emit(
        SocketConst.EMIT.POINTED_NOT_SAY_UNO,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.POINTED_NOT_SAY_UNO, err)
    )


def send_challenge(data):
    print('{} data_req:'.format(SocketConst.EMIT.CHALLENGE), data)
    sio.emit(
        SocketConst.EMIT.CHALLENGE,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.CHALLENGE, err)
    )


def send_special_logic(data):
    print('{} data_req:'.format(SocketConst.EMIT.SPECIAL_LOGIC), data)
    sio.emit(
        SocketConst.EMIT.SPECIAL_LOGIC,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.SPECIAL_LOGIC, err)
    )


def random_by_number(num):
    """
    乱数取得

    Args:
        num (int):

    Returns:
        int:
    """
    return math.floor(random.random() * num)


def get_card_play_valid(card_play_before, cards, must_call_draw_card):
    """
    card_play_beforeに基づき、プレイヤーの手札にある全てのカードを取得する関数です。
    cards_valid は Skip、Draw_2、Reverse で構成されています。#数字カードも含まれている気がする
    cards_wild は Wild と Wild_shuffle と White_wild で構成されています。
    cards_wild4 は Wild_draw_4 のみで構成されています。
    card_play_before is card before play of before Player.
    must_call_draw_card have value is true or false. If must_call_draw_card = true, Player only call event draw-card to draw more cards from Desk.
    """
    cards_wild4 = []
    cards_wild = []
    cards_wild_shuffle = []
    cards_white_wild= []
    cards_sabotage = []
    cards_reverse = []
    cards_number = []

    #強制的にカードを引く場合
    if str(must_call_draw_card) == 'True':
        return {
            'cardsWild4': cards_wild4,
            'cardsWild': cards_wild,
            'cardsWildshuffle': cards_wild_shuffle,
            'cardsWhiteWild':cards_white_wild,
            'cardsSabotage': cards_sabotage,
            'cardsReverse': cards_reverse,
            'cardsNumber': cards_number,
        }

    for card in cards:
        card_special = card.get('special')
        card_number = card.get('number')
        if str(card_special) == Special.WILD_DRAW_4:
            cards_wild4.append(card)
        elif str(card_special) == Special.WILD:
            cards_wild.append(card)
        elif str(card_special) == Special.WILD_SHUFFLE:
            cards_wild_shuffle.append(card)
        elif str(card_special) == Special.WHITE_WILD:
            cards_white_wild.append(card)
        # card_specialが空ではない and (場札と色が同じ or 場札と記号が同じ)
        # wild系は全て上で引っかかるのでdraw2，skip，reverseだけになるはず
        elif (card_special is not None and
             (str(card.get('color')) == str(card_play_before.get('color')) or 
              str(card_special) == str(card_play_before.get('special')))):
            if (str(card_special) == Special.DRAW_2 or str(card_special) == Special.SKIP):
                cards_sabotage.append(card)
            elif str(card_special) == Special.REVERSE:
                cards_reverse.append(card)
        # card_numberが空ではない（？） and (場札と色が同じ or 場札と数字が同じ)
        elif ((card_number is not None or (card_number is not None and int(card_number) == 0)) and
             ((card_play_before.get('number') and int(card_number) == int(card_play_before.get('number'))) or
              (str(card.get('color')) == str(card_play_before.get('color'))))):
            cards_number.append(card)

    return cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number

def remove_card_of_player(card_play, cards_of_player):
    """
    プレイヤーのカードを削除する機能。
    例：プレイヤー1が赤9と黄8の2枚のカードを持っている。プレイヤー1が赤9をプレイ→プレイヤー1は黄8を残す。
    """
    is_remove = False
    new_cards_of_player = []
    for card_validate in cards_of_player:
        if is_remove:
            new_cards_of_player.append(card_validate)
            continue
        elif card_play.get('special'):
            if card_play.get('color') == card_validate.get('color') and card_play.get('special') == card_validate.get('special'):
                is_remove = True
                continue
            else:
                new_cards_of_player.append(card_validate)
                continue
        else:
            if (
                card_play.get('color') == card_validate.get('color') and
                card_play.get('number') is not None and card_validate.get('number') is not None and
                int(card_play.get('number')) == int(
                    card_validate.get('number'))
            ):
                is_remove = True
                continue
            else:
                new_cards_of_player.append(card_validate)
                continue
    return new_cards_of_player


def remove_card_of_player(card_play, cards_of_player):
    """
    プレイヤーのカードを削除する機能。
    例：プレイヤー1が赤9と黄8の2枚のカードを持っている。プレイヤー1が赤9をプレイ→プレイヤー1は黄8を残す。
    """
    is_remove = False
    new_cards_of_player = []
    for card_validate in cards_of_player:
        if is_remove:
            new_cards_of_player.append(card_validate)
            continue
        elif card_play.get('special'):
            if card_play.get('color') == card_validate.get('color') and card_play.get('special') == card_validate.get('special'):
                is_remove = True
                continue
            else:
                new_cards_of_player.append(card_validate)
                continue
        else:
            if (
                card_play.get('color') == card_validate.get('color') and
                card_play.get('number') is not None and card_validate.get('number') is not None and
                int(card_play.get('number')) == int(
                    card_validate.get('number'))
            ):
                is_remove = True
                continue
            else:
                new_cards_of_player.append(card_validate)
                continue
    return new_cards_of_player
    
#数字カードを出す時の処理
def execute_play_number(total, play_cards):
    number = []
    for i in range(len(play_cards)):
        number.append(int(play_cards[i].get('number')))
    max_value = max(number)
    max_index = number.index(max_value)
    card_play = play_cards[max_index]
    data = {
        'card_play': card_play,
    }
        #変更なし
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_play_card(data)
    else:
        # call event play-card
        send_play_card(data)

#カードを出す　変更あり
def execute_play_sabotage(total, play_cards):
    """
    カードを出す

    Args:
        total (int): 手札の総数
        play_cards (list): 場に出す候補のカードリスト
    """
    for j in range(len(play_cards)):
        if play_cards[j].get('special')==Special.DRAW_2:
            card_play=play_cards[j]
            break
    for i in range(len(play_cards)):
        if play_cards[i].get('special')==Special.SKIP:
            card_play=play_cards[i] 
            break
    data = {
        'card_play': card_play,
    }
    #変更なし
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_play_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_reverse(total, play_cards):
    global draw_id
    draw_id=''
    card_play = play_cards[0]
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_play_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_reverse_same_color(total, cards_reverse, card_play_before):
    global draw_id
    draw_id=''
    for i in range(len(cards_reverse)):
        if cards_reverse[i].get('color')==card_play_before.get('color'):
            card_play = cards_reverse[i]
            break
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_play_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_wild(total, play_cards):

    card_play = play_cards[0]
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_play_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_white_wild(total, play_cards):
    card_play = play_cards[0]
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_play_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_color_change(total, play_cards, card_play_before):
    for i in range(len(play_cards)):
        if card_play_before.get('color')!=play_cards[i].get('color'):
            card_play=play_cards[i]
            break
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_play_card(data)
    else:
        # call event play-card
        send_play_card(data)

#Next_playerがUNO状態の時に出せない色のナンバーカードを出して邪魔する
def execute_play_color_sabotage(total, cards_number):
    card_play=[]
    for i in range(len(cards_number)):
        if cards_number[i].get('color')==color_check.get(next_id):
            card_play.append(cards_number[i])
    execute_play_number(total, card_play)

#変更の必要性がないかも
def determine_if_execute_pointed_not_say_uno(number_card_of_player):
  global uno_declared

  target = None
  for k, v in number_card_of_player.items():
    if v == 1:
      target = k
      break
    elif k in uno_declared:
      del uno_declared[k]
  
  if (
    target is not None and
    target != id and
    target not in uno_declared.keys()
  ):
    send_pointed_not_say_uno({
        'target': target,
    })
    time.sleep(TIME_DELAY / 1000)

#手札の中でSKIPとDRAW2とナンバーのペアがあるかどうか
#skipとdraw2のペアはnumberじゃなくてもいいのでは．
def sabotage_and_number(cards):
    skip_seq=[]
    draw2_seq=[]
    num_seq=[]
    for i in range(len(cards)):
        for j in range(len(cards)):
            if i==j:
                continue
            if cards[i].get('special')==Special.SKIP and cards[i].get('color')==cards[j].get('color') and cards[j].get('number') is not None:
                skip_seq.append(i)
                num_seq.append(j)
                break
            elif cards[i].get('special')==Special.DRAW_2 and cards[i].get('color')==cards[j].get('color') and cards[j].get('number') is not None:
                draw2_seq.append(i)
                num_seq.append(j)
                break
        else:
            continue
        break
    if len(skip_seq)>0:
        return skip_seq[0],num_seq[0]
    elif len(draw2_seq)>0:
        return draw2_seq[0],num_seq[0]
    else:
        return False,False

#手札の最小値を算出（自分のidのときは省きたい）
def min_research(number_card_of_player):
    number = []
    for num in number_card_of_player.values():
        number.append(int(num))
    min_value = min(number)
    return min_value
#手札のスペシャルカード枚数を取得
def special_count(cards):
    count=0
    for card in cards:
        if card.get('special') is not None:
            count=count+1
    return count
#場札の色を決定(wild)
def select_color_of_wild(cards):
    color=[0,0,0,0]
    for i in range(len(cards)):
        if cards[i].get('color')==Color.RED:
            color[0]=color[0]+1
        elif cards[i].get('color')==Color.YELLOW:
            color[1]=color[1]+1
        elif cards[i].get('color')==Color.GREEN:
            color[2]=color[2]+1
        elif cards[i].get('color')==Color.BLUE:
            color[3]=color[3]+1
    max_value = max(color)
    max_index = color.index(max_value)
    return max_index

def select_color_of_number(cards):
    color=[0,0,0,0]
    for i in range(len(cards)):
        if cards[i].get('color')==Color.RED:
            color[0]=color[0]+1
        elif cards[i].get('color')==Color.YELLOW:
            color[1]=color[1]+1
        elif cards[i].get('color')==Color.GREEN:
            color[2]=color[2]+1
        elif cards[i].get('color')==Color.BLUE:
            color[3]=color[3]+1
    min_color=[i for i in color if i!=0]
    if len(min_color)>0:
        min_value = min(min_color)
        min_index = color.index(min_value)
        return min_index
    else:
        return 0


def cards_number_change(cards_number,card_play_before):
    for i in range(len(cards_number)):
        if card_play_before.get('color')!=cards_number[i].get('color'):
            return True
    return False

def cards_sabotage_change(cards_sabotage,card_play_before):
    for i in range(len(cards_sabotage)):
        if card_play_before.get('color')!=cards_sabotage[i].get('color'):
            return True
    return False

#邪魔でreverseを出すときに同じ色のreverseがあるかどうか
def check_cards_reverse(cards_reverse,card_play_before):
    for i in range(len(cards_reverse)):
        if cards_reverse[i].get('color')==card_play_before.get('color'):
            return True
    return False

#保守
def conservative(data_res,cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number):
    global draw_id
    draw_id=''
    cards = data_res.get('card_of_player')
    # average_cards_number = sum([int(i) for i in data_res.get('number_card_of_player').values()])/4
    if len(cards_wild_shuffle)>0:
        execute_play_wild(len(cards), cards_wild_shuffle)
    elif len(cards_white_wild)>0:
        execute_play_white_wild(len(cards), cards_white_wild)
    elif len(cards_wild)>0:
        execute_play_wild(len(cards), cards_wild)
    elif len(cards_sabotage)>0:
        execute_play_sabotage(len(cards),cards_sabotage)
    elif len(cards_reverse)>0:
        execute_play_reverse(len(cards),cards_reverse)
    elif len(cards_number)>0:
        execute_play_number(len(cards),cards_number)
    elif len(cards_wild4)>0:
        execute_play_wild(len(cards), cards_wild4)
    else:
        active(data_res,cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number)
        return

def number_count(cards):
    count=0
    for card in cards:
        if card.get('number') is not None:
            count=count+1
    return count

#攻撃
# def active(data_res, cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number):
#     cards = data_res.get('card_of_player')
#     average_cards_number = sum([int(i) for i in data_res.get('number_card_of_player').values()])/4
#     card_play_before = data_res.get('card_before', {})
#     color_min = ARR_COLOR[select_color_of_number(cards)]
#     #要確認
#     if len(cards_wild_shuffle) > 0 and len(cards)-1 > average_cards_number and (len(cards_wild4) + len(cards_wild) + len(cards_sabotage) <= len(cards)-average_cards_number-1):
#         execute_play_wild(len(cards), cards_wild_shuffle)
#     elif len(cards_reverse)>0:
#         execute_play_reverse(len(cards),cards_reverse)
#     #要確認
#     elif (len(cards_number)>0 and number_count(cards)>1) and cards_number_change(cards_number,card_play_before) and (card_play_before.get('color') == str(color_min)):
#         execute_play_number_color_change(len(cards), cards_number,card_play_before)
#     elif len(cards_number)>0 and number_count(cards)>1:
#         execute_play_number(len(cards),cards_number)
#     elif len(cards_sabotage)>0:
#         execute_play_sabotage(len(cards),cards_sabotage)
#     elif len(cards_wild)>0:
#         execute_play_wild(len(cards), cards_wild)
#     #これであがり
#     elif len(cards_number)>0:
#         execute_play_number(len(cards),cards_number)
#     elif len(cards_wild4)>0:
#         execute_play_wild(len(cards), cards_wild4)
#     else:
#         send_draw_card({})

def active(data_res, cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number):
    global draw_id
    draw_id=''
    cards = data_res.get('card_of_player')
    average_cards_number = sum([int(i) for i in data_res.get('number_card_of_player').values()])/4
    card_play_before = data_res.get('card_before', {})
    color_min = ARR_COLOR[select_color_of_number(cards)]
    if len(cards_wild4)>0 or len(cards_wild)>0:
        if len(cards_wild_shuffle)>0:
            if len(cards_wild4)>0 and len(cards_wild)>0 and len(cards_white_wild)>0:
                execute_play_white_wild(len(cards), cards_white_wild)
            elif len(cards_wild4)>0 and len(cards_white_wild)>0:
                execute_play_white_wild(len(cards), cards_white_wild)
            elif len(cards_wild)>0 and len(cards_white_wild)>0:
                execute_play_white_wild(len(cards), cards_white_wild)
            elif len(cards_wild4)>0 and len(cards_wild)>0:
                execute_play_wild(len(cards), cards_wild)
            elif len(cards_reverse)>0:
                execute_play_reverse(len(cards),cards_reverse)
            elif len(cards_number)>0 and cards_number_change(cards_number,card_play_before) and (card_play_before.get('color') == str(color_min)):
                execute_play_color_change(len(cards), cards_number,card_play_before)
            elif len(cards_sabotage)>0 and cards_sabotage_change(cards_sabotage,card_play_before) and (card_play_before.get('color') == str(color_min)):
                execute_play_color_change(len(cards), cards_sabotage,card_play_before)
            elif len(cards_sabotage)>0:
                execute_play_sabotage(len(cards),cards_sabotage)
            elif len(cards_number)>0:
                execute_play_number(len(cards),cards_number)
            elif len(cards_wild)>0:
                execute_play_wild(len(cards),cards_wild)
            elif len(cards_white_wild)>0:
                execute_play_white_wild(len(cards),cards_white_wild)
            elif len(cards_wild_shuffle)>0 and len(cards)-1 > average_cards_number:
                execute_play_wild(len(cards),cards_wild_shuffle)
            elif len(cards_wild4)>0:
                execute_play_wild(len(cards),cards_wild4)
            elif len(cards_wild_shuffle)>0 and len(cards)==1:
                execute_play_wild(len(cards),cards_wild_shuffle)
            else:
                send_draw_card({})
        else:
            if len(cards_reverse)>0:
                execute_play_reverse(len(cards),cards_reverse)
            elif len(cards_wild4)>0 and len(cards_wild)>0 and len(cards_white_wild)>0:
                execute_play_white_wild(len(cards), cards_white_wild)
            elif len(cards_sabotage)>0 and cards_sabotage_change(cards_sabotage,card_play_before) and (card_play_before.get('color') == str(color_min)):
                execute_play_color_change(len(cards), cards_sabotage,card_play_before)
            elif len(cards_number)>0 and cards_number_change(cards_number,card_play_before) and (card_play_before.get('color') == str(color_min)):
                execute_play_color_change(len(cards), cards_number,card_play_before)
            elif len(cards_sabotage)>0:
                execute_play_sabotage(len(cards),cards_sabotage)
            elif len(cards_number)>0:
                execute_play_number(len(cards),cards_number)
            elif len(cards_wild4)>0 and len(cards_white_wild)>0:
                execute_play_white_wild(len(cards), cards_white_wild)
            elif len(cards_wild)>0 and len(cards_white_wild)>0:
                execute_play_white_wild(len(cards), cards_white_wild)
            elif len(cards_wild4)>0 and len(cards_wild)>0:
                execute_play_wild(len(cards), cards_wild)
            elif len(cards_wild)>0:
                execute_play_wild(len(cards),cards_wild)
            elif len(cards_white_wild)>0:
                execute_play_white_wild(len(cards),cards_white_wild)
            elif len(cards_wild4)>0:
                execute_play_wild(len(cards),cards_wild4)
            else:
                send_draw_card({})  
    else:
        if len(cards_wild_shuffle)>0 and len(cards)-1 >= average_cards_number:
            execute_play_wild(len(cards),cards_wild_shuffle)
        elif len(cards_reverse)>0:
            execute_play_reverse(len(cards),cards_reverse)
        elif len(cards_sabotage)>0 and cards_sabotage_change(cards_sabotage,card_play_before) and (card_play_before.get('color') == str(color_min)):
            execute_play_color_change(len(cards), cards_sabotage,card_play_before)
        elif len(cards_sabotage)>0:
            execute_play_sabotage(len(cards),cards_sabotage)
        elif len(cards_number)>0 and cards_number_change(cards_number,card_play_before) and (card_play_before.get('color') == str(color_min)):
            execute_play_color_change(len(cards), cards_number,card_play_before)
        elif len(cards_number)>0:
            execute_play_number(len(cards),cards_number)
        elif len(cards_white_wild)>0:
            execute_play_white_wild(len(cards),cards_white_wild)
        elif len(cards_wild_shuffle)>0 and len(cards)==1:
            execute_play_wild(len(cards),cards_wild_shuffle)
        else:
            send_draw_card({})

@sio.on('connect')
def on_connect():
    print('Client connect successfully!')

    def join_room_callback(*args):
        global once_connected, id
        if args[0]:
            print('Client join room failed!')
            print(args[0])
            sio.disconnect()
        else:
            print('Client join room successfully!')
            print(args[1])
            once_connected = True
            id = args[1].get('your_id')

    if not once_connected:
        if is_test_tool:
            if not event_name:
                print('Not found event name')

            event_data = TEST_TOOL_EVENT_DATA.get(event_name, None)
            if event_name and not event_data:
                print('Undefined event name')

            if event_name == SocketConst.EMIT.JOIN_ROOM:
                send_join_room(event_data, join_room_callback)
                return
            if event_name == SocketConst.EMIT.COLOR_OF_WILD:
                send_color_of_wild(event_data)
                return
            if event_name == SocketConst.EMIT.PLAY_CARD:
                send_play_card(event_data)
                return
            if event_name == SocketConst.EMIT.DRAW_CARD:
                send_draw_card(event_data)
                return
            if event_name == SocketConst.EMIT.PLAY_DRAW_CARD:
                send_play_draw_card(event_data)
                return
            if event_name == SocketConst.EMIT.CHALLENGE:
                send_challenge(event_data)
                return
            if event_name == SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD:
                send_say_uno_and_play_card(event_data)
                return
            if event_name == SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD:
                send_say_uno_and_play_draw_card(event_data)
                return
            if event_name == SocketConst.EMIT.POINTED_NOT_SAY_UNO:
                send_pointed_not_say_uno(event_data)
                return
            if event_name == SocketConst.EMIT.SPECIAL_LOGIC:
                send_special_logic(event_data)
                return
        else:
            data_join_room = {
                'room_name': room_name,
                'player': player
            }
            send_join_room(data_join_room, join_room_callback)
            return


@sio.on('disconnect')
def on_disconnect():
    print('Client disconnect:')
    os._exit(0)


@sio.on(SocketConst.EMIT.JOIN_ROOM)
def on_join_room(data_res):
    print('join room: data_res:', data_res)


@sio.on(SocketConst.EMIT.RECEIVER_CARD)
def on_receiver_card(data_res):
    global cards_global
    print('{} receive cards: '.format(id))
    print(data_res)
    if data_res.get('player') == id:
        cards_global = cards_global + data_res.get('cards_receive', [])
        print('{} cards_global: '.format(
            SocketConst.EMIT.RECEIVER_CARD), cards_global)


@sio.on(SocketConst.EMIT.FIRST_PLAYER)
def on_first_player(data_res):
    global color_check
    global left_id
    global right_id
    global is_wild_sabotage
    global draw_id
    draw_id=''
    # global turn_right

    # #first_cardがreverseの時左回り
    # if data_res.get('first_card').get('special') == Special.REVERSE:
    #     turn_right=not turn_right

    #初期化
    is_wild_sabotage=False
    color_check={data_res.get('play_order')[0]:None,data_res.get('play_order')[1]:None,data_res.get('play_order')[2]:None,data_res.get('play_order')[3]:None}

    play_order=data_res.get('play_order')
    for i in range(len(play_order)):
        if play_order[i]==id:
            left_id=play_order[(i+1)%4]
            right_id=play_order[(i-1)%4]
            break
    
    print('{} is first player.'.format(data_res.get('first_player')))
    print(data_res)


#場札の色を変更（d）
@sio.on(SocketConst.EMIT.COLOR_OF_WILD)
def on_color_of_wild(data_res):
    global cards_global
    global is_wild_sabotage
    global color_check

    if is_wild_sabotage:
        data = {
            'title': 'aaaaaa',
            }
        send_special_logic(data)
        color_of_wild = color_check.get(next_id)
    elif len(cards_global)>0:
        color_of_wild = ARR_COLOR[select_color_of_wild(cards_global)]
    else:
        data = {
            'title': 'cccccc',
            }
        send_special_logic(data)
        color_of_wild = ARR_COLOR[0]
    data = {
        'color_of_wild': color_of_wild,
    }
    send_color_of_wild(data)


@sio.on(SocketConst.EMIT.UPDATE_COLOR)
def on_update_color(data_res):
    global current_card
    current_card['color'] = data_res.get('color')
    print('update reveal card color is {}.'.format(data_res.get('color')))
    print(data_res)


@sio.on(SocketConst.EMIT.SHUFFLE_WILD)
def on_suffle_wild(data_res):
    global cards_global, uno_declared
    print('{} receive cards from shuffle wild.'.format(id))
    print(data_res)
    cards_global = data_res.get('cards_receive')
    uno_declared = {}
    for k, v in data_res.get('number_card_of_player').items():
        if v == 1:
            uno_declared[data_res.get('player')] = True
            break
        elif k in uno_declared:
            del uno_declared[k]
    print('{} cards_global:'.format(
        SocketConst.EMIT.SHUFFLE_WILD), cards_global)


#場札にカードを出す（p）
@sio.on(SocketConst.EMIT.PLAY_CARD)
def on_play_card(data_res):
    global cards_global
    global current_card

    card_play = data_res.get('card_play')
    #UPDATEイベントで追記する
    current_card = data_res.get('card_play')

    print(
        '{} play card {} {}.'.format(
            data_res.get('player'), card_play.get('color'), card_play.get('special') or card_play.get('number'))
    )
    print('{} data_res:'.format(SocketConst.EMIT.PLAY_CARD), data_res)
    if data_res.get('player') == id and card_play:
        cards_global = remove_card_of_player(card_play, cards_global)
        print('cards_global after:', cards_global)

#山札からカードを引く（p）
@sio.on(SocketConst.EMIT.DRAW_CARD)
def on_draw_card(data_res):
    global draw_id
    global color_check
    global current_card

    if current_card.get('special')!=Special.DRAW_2 and current_card.get('special')!=Special.WILD_DRAW_4 and current_card.get('special')!=Special.WHITE_WILD:
        draw_id=data_res.get('player')
        color_check[draw_id]=current_card.get('color')
    print('{} data_res:'.format(SocketConst.EMIT.DRAW_CARD), data_res)
    if data_res.get('player') == id:
        if data_res.get('can_play_draw_card'):
            if len(cards_global)==2:
                data = {}
                send_say_uno_and_play_draw_card(data)
            else:
                print('{} data_req:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), {
                    'is_play_card': True
                })
                data = {
                    'is_play_card': True
                }
                send_play_draw_card(data)
        else:
            print('{} can not play draw card.'.format(data_res.get('player')))

@sio.on(SocketConst.EMIT.PLAY_DRAW_CARD)
def on_play_draw_card(data_res):
    global cards_global
    print('{} data_res:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), data_res)
    print('{} play draw card.'.format(data_res.get('player')))
    if data_res.get('player') == id and data_res.get('is_play_card') == True:
        cards_global = remove_card_of_player(
            data_res.get('card_play'), cards_global)


@sio.on(SocketConst.EMIT.CHALLENGE)
def on_challenge(data_res):
    if data_res.get('is_challenge'):
        if data_res.get('is_challenge_success'):
            print('{} challenge successfully!'.format(
                data_res.get('challenger')))
        else:
            print('{} challenge failed!'.format(data_res.get('challenger')))
    else:
        print('{} no challenge.'.format(data_res.get('challenger')))


@sio.on(SocketConst.EMIT.PUBLIC_CARD)
def on_public_card(data_res):
    print('Public card of player {}.'.format(data_res.get('card_of_player')))
    print(data_res.get('cards'))


@sio.on(SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD)
def on_say_uno_and_play_card(data_res):
    global cards_global
    card_play = data_res.get('card_play', {})
    print(
        '{} play card {} {} and say UNO.'.format(
            data_res.get('player'), card_play.get('color'), card_play.get('special') or card_play.get('number'))
    )

    uno_declared[data_res.get('player')] = True

    if data_res.get('player') == id and card_play:
        cards_global = remove_card_of_player(card_play, cards_global)
        print('cards_global after: ', cards_global)


@sio.on(SocketConst.EMIT.SAY_UNO_AND_PLAY_DRAW_CARD)
def on_say_uno_and_play_draw_card(data_res):
    global cards_global
    card_play = data_res.get('card_play', {})
    print(
        '{} play draw card {} {} and say UNO.'.format(
            data_res.get('player'), card_play.get('color'), card_play.get('special') or card_play.get('number'))
    )

    uno_declared[data_res.get('player')] = True

    if data_res.get('player') == id:
        cards_global = remove_card_of_player(card_play, cards_global)
        print('cards_global after: ', cards_global)


@sio.on(SocketConst.EMIT.POINTED_NOT_SAY_UNO)
def on_pointed_not_say_uno(data_res):
    if str(data_res.get('have_say_uno')) == 'True':
        print('{} have say UNO.'.format(data_res.get('target')))
    elif str(data_res.get('have_say_uno')) == 'False':
        print('{} no say UNO.'.format(data_res.get('target')))


@sio.on(SocketConst.EMIT.FINISH_TURN)
def on_finish_turn(data_res):
    global cards_global
    if data_res.get('winner'):
        print('Winner turn {} is {}.'.format(
            data_res.get('turn_no'), data_res.get('winner')))
    else:
        print('Finish turn. No winner is this turn.')
    cards_global = []


@sio.on(SocketConst.EMIT.FINISH_GAME,)
def on_finish_game(data_res):
    print(data_res)
    print('Winner of game {}, turn win is {}.'.format(
        data_res.get('winner'), data_res.get('turn_win')))


@sio.on(SocketConst.EMIT.PENALTY,)
def on_finish_game(data_res):
    print(data_res)
    print('{} gets a penalty. Reason: {}'.format(
        data_res.get('player'), data_res.get('error')))
    if data_res.get('player') in uno_declared:
        del uno_declared[data_res.get('player')]


#次の順番のプレイヤーを通知
@sio.on(SocketConst.EMIT.NEXT_PLAYER)
def on_next_player(data_res):
    global cards_global
    global is_wild_sabotage
    global next_id
    # global is_draw
    global draw_id
    global left_id
    global right_id

    is_wild_sabotage=False
    if data_res.get('turn_right'):
        next_id=left_id
    else:
        next_id=right_id
    print('{} data_res: '.format(SocketConst.EMIT.NEXT_PLAYER), data_res)
    time.sleep(TIME_DELAY / 1000)
    print('{} is next player. turn: {}'.format(
        data_res.get('next_player'),
        data_res.get('number_turn_play')
    ))
    #number_card_of_playerは各プレイヤーの手札枚数
    #UNOといってないプレーヤーを指摘するかどうか決定する関数
    determine_if_execute_pointed_not_say_uno(data_res.get('number_card_of_player'))
    
    print('Run NEXT_PLAYER ...')
    # refresh cards_global
    #card_of_playerは自分の手札
    cards_global = data_res.get('card_of_player')
    print(cards_global)
    cards = cards_global
    #card_beforeは1つ前に捨てられたカード
    card_play_before = data_res.get('card_before', {})
    #draw_reasonはカードを引かなければいけない理由
    draw_reason = data_res.get('draw_reason')  

    #手札の中でSKIPとDRAW2とナンバーのペアがあるかどうか
    # is_sabotage_and_number=sabotage_and_number(cards)

    #手札の最小値
    min_player=min_research(data_res.get('number_card_of_player'))

    # play_wild_draw4_turnの直後のターンの場合 プレイの前にChallengeができます。
    # ただし、ホワイトワイルド（bind_2）の効果が発動している間はチャレンジができません。
    if (draw_reason == DrawReason.WILD_DRAW_4):
        # random challenge or not
        #基本チャレンジしない方針に変更したいね
        num_random = 0
        print('${SocketConst.EMIT.CHALLENGE} data_req:', {
            'is_challenge': True if num_random else False,
        })
        sio.emit(
            SocketConst.EMIT.CHALLENGE,
            {
                'is_challenge': False,
            },
            callback=lambda err, undefined: handle_error(
                SocketConst.EMIT.CHALLENGE, err)
        )

        # num_random = 1の場合、プレイの前にChallengeすることを意味します。そして、ディーラーからのChallengeの結果を待ちます。
        if num_random:
            return

    cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number = get_card_play_valid(
        card_play_before,
        cards,
        data_res.get('must_call_draw_card'),
    )

    special_card_count=special_count(cards)
    #1/10の確率でspecial_logicを発動
    # special_logic_num_random = random_by_number(10)
    # if special_logic_num_random == 0:
    #     data = {
    #         'title': SPECIAL_LOGIC_TITLE,
    #     }
    #     send_special_logic(data)
    #強制的にカードを引かなければならない場合
    if str(data_res.get('must_call_draw_card')) == 'True':
        # If must_call_draw_card = True, Player must be call event draw_card
        print('{} data_req:'.format(SocketConst.EMIT.DRAW_CARD), {
            'player': id,
        })
        send_draw_card({})
        return

    #邪魔
    if int(data_res.get('number_card_of_player').get(next_id))==1 and len(cards)>1:
        data = {
            'title': '邪魔モード',
            }
        send_special_logic(data)
        draw_id=''
        if len(cards_white_wild)>0:
            execute_play_white_wild(len(cards),cards_white_wild)
        elif len(cards_sabotage)>0:
            execute_play_sabotage(len(cards), cards_sabotage)
        elif len(cards_wild)>0 and color_check.get(next_id) is not None:
            data = {
            'title': 'あなたにはあがらせません！'+ARR_COLOR_KANJI.get(color_check.get(next_id))+'持ってないですよね．',
            }
            send_special_logic(data)
            is_wild_sabotage=True
            execute_play_wild(len(cards), cards_wild)
        #色チェンジするときだけにしていいかも
        elif len([i for i in range(len(cards_number)) if cards_number[i].get('color')==color_check.get(next_id)])>0:
            data = {
            'title': 'あなたにはあがらせません！'+ARR_COLOR_KANJI.get(color_check.get(next_id))+'持ってないですよね．',
            }
            send_special_logic(data)
            execute_play_color_sabotage(len(cards), cards_number)
        elif len(cards_wild_shuffle)>0:
            execute_play_wild(len(cards), cards_wild_shuffle)
        else:
            data = {
            'title': '保守邪魔',
            }
            send_special_logic(data)
            conservative(data_res, cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number)
    #前の人がdraw_cardした時reverseを出す（邪魔）修正する必要
    elif data_res.get('before_player')==draw_id and len(cards)>1:
        data = {
            'title': 'リバースモード',
            }
        send_special_logic(data)
        if len(cards_reverse)>0 and check_cards_reverse(cards_reverse,card_play_before):
            data = {
            'title': ARR_COLOR_KANJI.get(color_check.get(draw_id))+'持ってないんですね．もう１枚どうぞ！！',
            }
            send_special_logic(data)
            execute_play_reverse_same_color(len(cards), cards_reverse, card_play_before)
        elif min_player<=2 and len(cards)-min_player>=3:
            conservative(data_res,cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number)
        elif len(cards_wild4)>0 or len(cards_wild)>0 or len(cards_wild_shuffle)>0 or len(cards_white_wild)>0 or len(cards_sabotage)>0 or len(cards_reverse)>0 or len(cards_number)>0:
            active(data_res, cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number)
        else:
            send_draw_card({})
            return
    #保守
    elif min_player<=2 and len(cards)-min_player>=3:
        conservative(data_res,cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number)
    #攻め
    elif len(cards_wild4)>0 or len(cards_wild)>0 or len(cards_wild_shuffle)>0 or len(cards_white_wild)>0 or len(cards_sabotage)>0 or len(cards_reverse)>0 or len(cards_number)>0:
        active(data_res, cards_wild4, cards_wild, cards_wild_shuffle, cards_white_wild, cards_sabotage, cards_reverse, cards_number)
    else:
        send_draw_card({})
        return


@sio.on('*')
def catch_all(event, data):
    print('!! unhandled event: {} '.format(event), data)


def main():
    sio.connect(
        args.host,
        transports=['websocket'],
    )
    sio.wait()


if __name__ == '__main__':
    main()
