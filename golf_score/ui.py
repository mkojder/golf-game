import functools

from tkinter import *

import events
import game_state


class UI(Frame):
    def __init__(self, root, event_queue):
        super().__init__(root)
        self.root = root
        self.gs = game_state.GameState()
        self.event_queue = event_queue
        
        self.listbox = Listbox(self)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        for val in self.gs.get_all_players():
            self.listbox.insert(END, val)
        
        self.current = self.listbox.curselection()
        self.add_player_button = Button(self, text='Add Player', command=self.add_player_dialog)
        self.add_player_button.pack(side=LEFT)

        self.quit_button = Button(self, text='QUIT', command=self.quit)
        self.quit_button.pack(side=RIGHT)

        self.label = Label(self)
        self.set_label_text(self.gs)
        self.label.pack(side=LEFT)
        self.poll()

    def poll(self):
        if len(self.listbox.curselection()) == 0:
            self.listbox.selection_set(0)
            self.current = self.listbox.curselection()
        now = self.listbox.curselection()
        if now != self.current:
            self.selection_changed(self.listbox.get(now[0]))
            self.current = now
        self.after(250, self.poll)

    
    def add_player_dialog(self):
        top = self.top = Toplevel(self)
        Label(top, text='Name').pack()
        self.entry = Entry(top)
        self.entry.pack(padx=5)
        b = Button(top, text='OK', command=self.ok)
        b.pack(pady=5)
        self.entry.focus()
        self.top.grab_set()

    def ok(self):
        text = self.entry.get()
        if text.strip() != '':
            self.event_queue.put((events.EventTypes.SWITCH_PLAYER, self.entry.get()))
        self.top.grab_release()
        self.top.destroy()
    
    def selection_changed(self, new_value):
        self.event_queue.put((events.EventTypes.SWITCH_PLAYER, new_value))

    def set_label_text(self, gs):
        label_format = 'Made {}\n out of {}\n{}%'
        all_shots = gs.get_player_stats()
        made = all_shots.count(True)
        total = len(all_shots)
        ratio = made/total*100 if total != 0 else 0
        self.label['text'] = (label_format.format(made, total, str(round(ratio, 2))))

    def refresh(self, gs, is_new_player=False, current_player=None):
        self.set_label_text(gs)
        if current_player is not None:
            if is_new_player:
                self.listbox.delete(0, END)
                players = gs.get_all_players()
                for val in players:
                        self.listbox.insert(END, val)

            ind = self.listbox.get(0, END).index(current_player)
            self.listbox.selection_set(ind)

