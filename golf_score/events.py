from enum import Enum
import datetime
import queue

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

def event_loop(event_queue, ui):
    gs = game_state.GameState()
    ignore_period = None
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
                            break
                except queue.Empty as e:
                    print('event: missed shot! empty queue')
                    gs.add_shot(event[1], False)
                    break
            ui.refresh(gs)
        elif event[0] == EventTypes.SWITCH_PLAYER:
            player_switched_to, is_new_player = switch_player(gs, event[1])
            ui.refresh(gs, is_new_player, player_switched_to)
