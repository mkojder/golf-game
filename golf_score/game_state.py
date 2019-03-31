import os
import sqlite3



class GameState:

    def __init__(self, db_path='/home/pi/golf.db'):
        self.db_path = db_path
        if not os.path.exists(db_path):
            self.setup_new_db()
        else:
            self.conn = sqlite3.connect(
                db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            self.cursor = self.conn.cursor()
        self._current_player = self.get_default_player()

    def setup_new_db(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self.conn.cursor()
        cursor = self.cursor
        cursor.execute('''CREATE TABLE players
        (name text, uid text)
        ''')
        cursor.execute('''CREATE TABLE shots
        (datetime timestamp, player_name text, made integer)
        ''')
        self.conn.commit()
        self.add_new_player('Mike Kojder')

    def get_default_player(self):
        self.cursor.execute('SELECT name FROM players LIMIT 1')
        return self.cursor.fetchone()[0]

    def set_current_player(self, name):
        self.cursor.execute('''SELECT 
        EXISTS(SELECT 1 FROM players WHERE name=?)
        ''', (name,))
        if self.cursor.fetchone()[0]:
            self._current_player = name
        else:
            raise ValueError('Player: {} not found'.format(name))

    def get_current_player(self):
        return self._current_player

    def get_all_players(self):
        self.cursor.execute('SELECT name FROM players')
        return [x[0] for x in self.cursor.fetchall()]

    def add_new_player(self, name):
        self.cursor.execute('''INSERT INTO players VALUES 
        (?, '')
        ''', (name,))
        self.conn.commit()

    def get_player_from_uid(self, uid):
        self.cursor.execute('''SELECT name FROM players
        WHERE uid=?
        ''', (uid,))
        name = self.cursor.fetchone()
        if name is None:
            return None
        return name[0]

    def set_uid_for_player(self, uid, player=None):
        if player is None:
            player = self._current_player
        self.cursor.execute('''UPDATE players SET uid=?
        WHERE name=? 
        ''', (uid, player))
        self.conn.commit()

    def get_uid_for_player(self, player=None):
        if player is None:
            player = self._current_player
        self.cursor.execute('''SELECT uid FROM players
        WHERE name=?
        ''', (player,))
        uid = self.cursor.fetchone()
        if uid is None:
            raise ValueError('Player: {} not found'.format(player))
        return uid[0]

    def add_shot(self, dt, made_shot, player=None):
        if player is None:
            player = self._current_player
        self.cursor.execute('''INSERT INTO shots VALUES 
        (?, ?, ?)
        ''', (dt, player, made_shot))
        self.conn.commit()

    def get_all_player_stats(self, begin_inclusive=None, end_inclusive=None):
        q = 'SELECT name, SUM(made), COUNT(made) FROM players LEFT JOIN shots ON name = player_name GROUP BY name'
        params = []
        if begin_inclusive is not None or end_inclusive is not None:
            q += ' WHERE '
            if begin_inclusive is not None:
                q += 'datetime >= ?'
                params.append(begin_inclusive)
            if end_inclusive is not None:
                q += 'datetime <= ?' if begin_inclusive is None else ' AND datetime <= ?'
                params.append(end_inclusive)
        self.cursor.execute(q, params)
        return [x for x in self.cursor.fetchall()]

    def get_player_stats(self, player=None, begin_inclusive=None, end_inclusive=None):
        if player is None:
            player = self._current_player
        q = 'SELECT made FROM shots WHERE player_name=?'
        params = [player]
        if begin_inclusive is not None:
            q += ' AND datetime >= ?'
            params.append(begin_inclusive)
        if end_inclusive is not None:
            q += ' AND datetime <= ?'
            params.append(end_inclusive)
        self.cursor.execute(q, params)
        return [x[0] for x in self.cursor.fetchall()]

