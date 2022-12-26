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
        # メッセージの送受信
        NEW_MESSAGE = 'new-message'

        JOIN_ROOM = 'join-room'
        RECEIVER_CARD = 'receiver-card'
        FIRST_PLAYER = 'first-player'
        COLOR_OF_WILD = 'color-of-wild'
        SHUFFLE_WILD = 'shuffle-wild'
        NEXT_PLAYER = 'next-player'
        PLAY_CARD = 'play-card'
        DRAW_CARD = 'draw-card'
        PLAY_DRAW_CARD = 'play-draw-card'
        CHALLENGE = 'challenge'
        PUBLIC_CARD = 'public-card'
        SAY_UNO_AND_PLAY_CARD = 'say-uno-and-play-card'
        POINTED_NOT_SAY_UNO = 'pointed-not-say-uno'
        SPECIAL_LOGIC = 'special-logic'
        FINISH_TURN = 'finish-turn'
        FINISH_GAME = 'finish-game'


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

print ({
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

#場札の色を変更する
def send_color_of_wild(data):
    print('{} data_req:'.format(SocketConst.EMIT.COLOR_OF_WILD), data)
    sio.emit(
        SocketConst.EMIT.COLOR_OF_WILD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.COLOR_OF_WILD, err)
    )

#場札にカードを出す　execute_playを変更すればいいのでここは変更なし
def send_play_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.PLAY_CARD), data)
    sio.emit(
        SocketConst.EMIT.PLAY_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.PLAY_CARD, err)
    )

#カードを引く　data={} 変更なし
def send_draw_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.DRAW_CARD), data)
    sio.emit(
        SocketConst.EMIT.DRAW_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.DRAW_CARD, err)
    )

#引いたカードをそのまま出す　変更なし
def send_draw_play_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), data)
    sio.emit(
        SocketConst.EMIT.PLAY_DRAW_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.PLAY_DRAW_CARD, err)
    )

#UNOと言ってカードを出す　多分綴りが間違ってるdraw→play 変更なし
def send_say_uno_and_draw_card(data):
    print('{} data_req:'.format(SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD), data)
    sio.emit(
        SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD, err)
    )

#UNOと言ってないプレイヤーを指摘する
def send_pointed_not_say_uno(data):
    print('{} data_req:'.format(SocketConst.EMIT.POINTED_NOT_SAY_UNO), data)
    sio.emit(
        SocketConst.EMIT.POINTED_NOT_SAY_UNO,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.POINTED_NOT_SAY_UNO, err)
    )

#WILD_DRAW_4が出された場合にチャレンジする
def send_challenge(data):
    print('{} data_req:'.format(SocketConst.EMIT.CHALLENGE), data)
    sio.emit(
        SocketConst.EMIT.CHALLENGE,
        data,
        callback=lambda err, undefined: handle_error(
            SocketConst.EMIT.CHALLENGE, err)
    )

#スペシャルロジックを発動する
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

#カードを分類している　変更の可能性あり
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
    cards_sabotage = []
    cards_reverse = []
    cards_number = []

    #強制的にカードを引く場合
    if str(must_call_draw_card) == 'True':
        return {
            'cardsWild4': cards_wild4,
            'cardsWild': cards_wild,
            'cardsWildother': cards_wild_shuffle,
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
            cards_sabotage.append(card)
        # card_specialが空ではない and (場札と色が同じ or 場札と記号が同じ)
        # wild系は全て上で引っかかるのでdraw2，skip，reverseだけになるはず
        elif (card_special is not None and
               (str(card.get('color')) == str(card_play_before.get('color')) or 
               card_special and str(card_special) == str(card_play_before.get('special')))):
            if (str(card_special) == Special.DRAW_2 or
                str(card_special) == Special.SKIP):
                cards_sabotage.append(card)
            elif str(card_special) == Special.REVERSE:
                cards_reverse.append(card)

        # card_numberが空ではない（？） and (場札と色が同じ or 場札と数字が同じ)
        elif ((card_number is not None or (card_number is not None and int(card_number) == 0)) and
             ((card_play_before.get('number') and int(card_number) == int(card_play_before.get('number'))) or
              (str(card.get('color')) == str(card_play_before.get('color'))))):
            cards_number.append(card)

    return cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number


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
        send_say_uno_and_draw_card(data)
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
    for i in range(len(play_cards)):
        if play_cards[i].get('special')==Special.SKIP:
            card_play=play_cards[i] 
            break
    for j in range(len(play_cards)):
        if play_cards[j].get('special')==Special.DRAW_2:
            card_play=play_cards[j]
            break
    for k in range(len(play_cards)):
        if play_cards[k].get('special')==Special.WHITE_WILD:
            card_play=play_cards[k]
            break 
    data = {
        'card_play': card_play,
    }
    #変更なし
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_draw_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_reverse(total, play_cards):
    
    card_play = play_cards[random_by_number(len(play_cards))]
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_draw_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_wild(total, play_cards):

    card_play = play_cards[random_by_number(len(play_cards))]
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_draw_card(data)
    else:
        # call event play-card
        send_play_card(data)

def execute_play_number_color_change(total, play_cards, card_play_before):
    for i in range(len(play_cards)):
        if card_play_before.get('color')!=play_cards[i].get('color'):
            card_play=play_cards[i]
            break
    data = {
        'card_play': card_play,
    }
    if total == 2:
        # call event say-uno-and-play-card
        send_say_uno_and_draw_card(data)
    else:
        # call event play-card
        send_play_card(data)

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
            elif cards[i].get('special')==Special.DRAW_2 and cards[i].get('color')==cards[j].get('color') and cards[j].get('number') is not None:
                draw2_seq.append(i)
                num_seq.append(j)
    if len(skip_seq)>0:
        return skip_seq[0],num_seq[0]
    elif len(draw2_seq)>0:
        return draw2_seq[0],num_seq[0]
    else:
        return False

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
#場札の色を決定
def select_color_of_wild(cards):
    color=[0,0,0,0]
    # cards=data_res.get('card_of_player')
    for i in range(len(cards)):
        if cards.get('color')==Color.RED:
            color[0]=color[0]+1
        elif cards.get('color')==Color.YELLOW:
            color[1]=color[1]+1
        elif cards.get('color')==Color.GREEN:
            color[2]=color[2]+1
        elif cards.get('color')==Color.BLUE:
            color[3]=color[3]+1
    max_value = max(color)
    max_index = color.index(max_value)
    return max_index

def cards_number_change(cards_number,card_play_before):
    for i in range(len(cards_number)):
        if card_play_before.get('color')!=cards_number[i].get('color'):
            return cards_number[i]
    return False
#保守
def conservative(cards,cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number):
    if len(cards_wild)>0:
        execute_play_wild(len(cards), cards_wild)
        return
    elif len(cards_wild_shuffle)>0:
        execute_play_wild(len(cards), cards_wild_shuffle)
        return
    elif len(cards_sabotage)>0:
        execute_play_sabotage(len(cards),cards_sabotage)
        return
    elif len(cards_reverse)>0:
        execute_play_reverse(len(cards),cards_reverse)
        return
    elif len(cards_number)>0:
        execute_play_number(len(cards),cards_number)
        return
    elif len(cards_wild4)>0:
        execute_play_wild(len(cards), cards_wild4)
        return
    else:
        active(cards,cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number)
        return


#攻撃
def active(cards,cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number):
    color_of_wild = ARR_COLOR[select_color_of_wild(cards)]
    

    
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
                send_draw_play_card(event_data)
                return
            if event_name == SocketConst.EMIT.CHALLENGE:
                send_challenge(event_data)
                return
            if event_name == SocketConst.EMIT.SAY_UNO_AND_PLAY_CARD:
                send_say_uno_and_draw_card(event_data)
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
#p=プレイヤーが任意に発生させるイベント
#d=ディーラーが管理するイベント

#ゲームへの参加（p）
@sio.on(SocketConst.EMIT.JOIN_ROOM)
def on_join_room(data_res):
    print('join room: data_res:', data_res)

#カードを手札に追加（d）
@sio.on(SocketConst.EMIT.RECEIVER_CARD)
def on_receiver_card(data_res):
    global cards_global
    print('{} receive cards: '.format(id))
    print(data_res)
    if data_res.get('player') == id:
        cards_global = cards_global + data_res.get('cards_receive', [])
        print('{} cards_global: '.format(
            SocketConst.EMIT.RECEIVER_CARD), cards_global)

#対戦開始（d）
@sio.on(SocketConst.EMIT.FIRST_PLAYER)
def on_first_player(data_res):
    print('{} is first player.'.format(data_res.get('first_player')))
    print(data_res)

#場札の色を変更（d）　変更する
@sio.on(SocketConst.EMIT.COLOR_OF_WILD)
def on_color_of_wild(data_res):
    color_of_wild = ARR_COLOR[select_color_of_wild(data_res.get('card_of_player'))]
    data = {
        'color_of_wild': color_of_wild,
    }
    send_color_of_wild(data)

#手札のカードをシャッフル（d）
@sio.on(SocketConst.EMIT.SHUFFLE_WILD)
def on_suffle_wild(data_res):
    global cards_global
    print('{} receive cards from shuffle wild.'.format(id))
    print(data_res)
    cards_global = data_res.get('cards_receive')
    print('{} cards_global:'.format(
        SocketConst.EMIT.SHUFFLE_WILD), cards_global)

#場札にカードを出す（p）
@sio.on(SocketConst.EMIT.PLAY_CARD)
def on_play_card(data_res):
    global cards_global
    card_play = data_res.get('card_play')
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
    print('{} data_res:'.format(SocketConst.EMIT.DRAW_CARD), data_res)
    if data_res.get('player') == id:
        if data_res.get('can_play_draw_card'):
            print('{} data_req:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), {
                'is_play_card': True
            })
            data = {
                'is_play_card': True
            }
            send_draw_play_card(data)
        else:
            print('{} can not play draw card.'.format(data_res.get('player')))

#山札から引いたカードを場札に出す（p）
@sio.on(SocketConst.EMIT.PLAY_DRAW_CARD)
def on_play_draw_card(data_res):
    global cards_global
    print('{} data_res:'.format(SocketConst.EMIT.PLAY_DRAW_CARD), data_res)
    print('{} play draw card.'.format(data_res.get('player')))
    if data_res.get('player') == id and data_res.get('is_play_card') == True:
        cards_global = remove_card_of_player(
            data_res.get('card_play'), cards_global)

#チャレンジ（p）
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

#手札の公開（d）
@sio.on(SocketConst.EMIT.PUBLIC_CARD)
def on_public_card(data_res):
    print('Public card of player {}.'.format(data_res.get('card_of_player')))
    print(data_res.get('cards'))

#UNOコールをし，カードを場札に出す（p）
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

#UNOコールを忘れていることを指摘（p）
@sio.on(SocketConst.EMIT.POINTED_NOT_SAY_UNO)
def on_pointed_not_say_uno(data_res):
    if str(data_res.get('have_say_uno')) == 'True':
        print('{} have say UNO.'.format(data_res.get('player')))
    elif str(data_res.get('have_say_uno')) == 'False':
        print('{} no say UNO.'.format(data_res.get('player')))

#対戦終了の通知（d）
@sio.on(SocketConst.EMIT.FINISH_TURN)
def on_finish_turn(data_res):
    global cards_global
    if data_res.get('winner'):
        print('Winner turn {} is {}.'.format(
            data_res.get('turn_no'), data_res.get('winner')))
    else:
        print('Finish turn. No winner is this turn.')
    cards_global = []

#ゲーム終了の通知（d）
@sio.on(SocketConst.EMIT.FINISH_GAME)
def on_finish_game(data_res):
    print(data_res)
    print('Winner of game {}, turn win is {}.'.format(
        data_res.get('winner'), data_res.get('turn_win')))

#次の順番のプレイヤーを通知
@sio.on(SocketConst.EMIT.NEXT_PLAYER)
def on_next_player(data_res):
    global cards_global
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
        num_random = random_by_number(2)
        print('${SocketConst.EMIT.CHALLENGE} data_req:', {
            'is_challenge': True if num_random else False,
        })
        sio.emit(
            SocketConst.EMIT.CHALLENGE,
            {
                'is_challenge': True if num_random else False,
            },
            callback=lambda err, undefined: handle_error(
                SocketConst.EMIT.CHALLENGE, err)
        )

        # num_random = 1の場合、プレイの前にChallengeすることを意味します。そして、ディーラーからのChallengeの結果を待ちます。
        if num_random:
            return

    cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number = get_card_play_valid(
        card_play_before,
        cards,
        data_res.get('must_call_draw_card'),
    )
    special_card_count=special_count(cards)
    #1/10の確率でspecial_logicを発動
    special_logic_num_random = random_by_number(10)
    if special_logic_num_random == 0:
        data = {
            'title': SPECIAL_LOGIC_TITLE,
        }
        send_special_logic(data)
    #強制的にカードを引かなければならない場合
    if str(data_res.get('must_call_draw_card')) == 'True':
        # If must_call_draw_card = True, Player must be call event draw_card
        print('{} data_req:'.format(SocketConst.EMIT.DRAW_CARD), {
            'player': id,
        })
        send_draw_card({})
        return

    #邪魔
    if int(data_res.get('number_card_of_player').get(data_res.get('next_player')))==1:
        if len(cards_sabotage)>0:
            execute_play_sabotage(len(cards), cards_sabotage)
            return
        elif len(cards_reverse)>0:
            execute_play_reverse(len(cards), cards_reverse)
            return
        elif len(cards_wild)>0:#一番手札の多い色に変更
            execute_play_wild(len(cards), cards_wild)
            return
        elif cards_number_change(cards_number,card_play_before):
            execute_play_number_color_change(len(cards), cards_number,card_play_before)
            return
        else:
            conservative(cards,cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number)
    #保守
    elif min_player <= 3 and min_player <= special_card_count:
        conservative(cards,cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number)
    #攻め
    elif len(cards_wild4)>0 or len(cards_wild)>0 or len(cards_wild_shuffle)>0 or  len(cards_sabotage)>0 or len(cards_reverse)>0 or len(cards_number)>0:
        active(cards,cards_wild4, cards_wild, cards_wild_shuffle, cards_sabotage, cards_reverse, cards_number)
    else:
        send_draw_card({})
        return

        
    # elif len(cards_reverse)>0:
    #     execute_play(len(cards), cards_reverse)
    #     return
    # elif is_sabotage_and_number:
    #     execute_play(len(cards), cards_reverse)
    #     return
    # elif not is_sabotage_and_number:

    # else:
    #     """
    #     有効なカードがない場合、プレイヤーはイベントDRAW_CARDを呼び出す必要があります。
    #     詳細はプレイヤー仕様書を参照してください。
    #     """
    #     send_draw_card({})
    #     return


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
