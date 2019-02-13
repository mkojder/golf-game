from enum import Enum
import datetime
import functools
import json
import queue

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

import game_state

class EventTypes(Enum):
    USB_MOTION0 = "USB_MOTION0"
    USB_MOTION1 = "USB_MOTION1"
    PICAM_MOTION = "PICAM_MOTION"
    SWITCH_PLAYER = "SWITCH_PLAYER"
    IGNORE_PERIOD = "IGNORE_PERIOD"


class ThreadKill:
    def __init__(self):
        self._kill = False

    def kill(self):
        self._kill = True

    def is_kill(self):
        return self._kill

def switch_player(gs, name):
    print('event: switch player')
    add_new = False
    if name not in gs.get_all_players():
        gs.add_new_player(name)
        add_new = True
    gs.set_current_player(name)
    return name, add_new

def aws_switch_player(gs, ui, client, userdata, message):
    payload = json.loads(message.payload)
    player_switched_to, is_new_player = switch_player(gs, payload['player'])
    ui.refresh(gs, is_new_player, player_switched_to)
    myMQTTClient.publish('golf/update', json.dumps(get_message_dict(gs)), 0)

def aws_ping(gs, client, userdata, message):
    myMQTTClient.publish('golf/update', json.dumps(get_message_dict(gs)), 0)

def get_message_dict(gs, made=None):
    d = {}
    text = "{} made {}\n out of {}\n{}%"
    player_stats = gs.get_all_player_stats()
    current_player = gs.get_current_player()
    d['currentPlayer'] = current_player
    p_list = []
    for row in player_stats:
        if row[0] == current_player:
            text = text.format(row[0], row[1], row[2], round(((row[1] / row[2]) * 100) if row[2] != 0 else 0, 2))
        p_list.append({'name': row[0], 'made': row[1], 'ratio': (row[1] / row[2]) if row[2] != 0 else 0})
    d['display'] = text
    d['players'] = p_list
    if made is not None:
        d['madeShot'] = made
    return d
        

def event_loop(event_queue, ui):
    gs = game_state.GameState()
    ignore_period = None

    # For certificate based connection
    myMQTTClient = AWSIoTMQTTClient("pi")
    # For Websocket connection
    # myMQTTClient = AWSIoTMQTTClient("myClientID", useWebsocket=True)
    # Configurations
    # For TLS mutual authentication
    myMQTTClient.configureEndpoint("a1h19cgwtbfelq-ats.iot.us-west-2.amazonaws.com", 8883)
    # For Websocket
    # myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 443)
    # For TLS mutual authentication with TLS ALPN extension
    # myMQTTClient.configureEndpoint("YOUR.ENDPOINT", 443)
    myMQTTClient.configureCredentials("ca.pem", "41fce67d5c-private.pem.key", "41fce67d5c-certificate.pem.crt")
    # For Websocket, we only need to configure the root CA
    # myMQTTClient.configureCredentials("YOUR/ROOT/CA/PATH")
    myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
    myMQTTClient.subscribe('golf/switchPlayer', 0, functools.partial(aws_switch_player, gs, ui))
    myMQTTClient.subscribe('golf/ping', 0, functools.partial(aws_ping, gs))
    while True:
        print('event: event_queue waiting')
        event = event_queue.get()
        if event is None:
            return  # Poison pill
        elif event[0] == EventTypes.IGNORE_PERIOD:
            print('event:ignore period')
            ignore_period = event[1]
        elif event[0] == EventTypes.USB_MOTION0 and (ignore_period is None or event[1] - ignore_period > datetime.timedelta(seconds=4)):
            print('event:start motion')
            remaining_time = datetime.timedelta(seconds=3.75)
            while True:
                try:
                    next_event = event_queue.get(timeout=remaining_time.total_seconds())
                    if event[0] == EventTypes.SWITCH_PLAYER:
                        switch_player(gs, event[1])
                    else:
                        remaining_time -= next_event[1] - event[1]
                        if next_event is None:
                            return # More poison ppill
                        elif remaining_time.total_seconds() < 0 or next_event[0] == EventTypes.PICAM_MOTION:
                            raise queue.Empty()
                        elif next_event[0] == EventTypes.USB_MOTION1:
                            print('event: made shot!')
                            gs.add_shot(event[1], True)
                            myMQTTClient.publish('golf/update', json.dumps(get_message_dict(gs, True)), 0)
                            break
                except queue.Empty as e:
                    print('event: missed shot! empty queue')
                    gs.add_shot(event[1], False)
                    myMQTTClient.publish('golf/update', json.dumps(get_message_dict(gs, False)), 0)
                    break
            ui.refresh(gs)
        elif event[0] == EventTypes.SWITCH_PLAYER:
            player_switched_to, is_new_player = switch_player(gs, event[1])
            ui.refresh(gs, is_new_player, player_switched_to)
            myMQTTClient.publish('golf/update', json.dumps(get_message_dict(gs)), 0)
