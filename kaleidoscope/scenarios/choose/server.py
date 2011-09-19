from os.path import dirname, join
from kaleidoscope.scenario import KalScenarioServer
from kivy.utils import get_color_from_hex
from kivy.core.image import Image
from kivy.clock import Clock
from math import cos

MIN_PLAYERS = 1

btnbg = Image(join(dirname(__file__), 'buttonbackground.png')).texture

from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, BorderImage
from kivy.core.window import Window

class ChooseView(FloatLayout):
    def __init__(self, **kwargs):
        super(ChooseView, self).__init__(**kwargs)
        c1 = get_color_from_hex('#96be25aa')
        c2 = get_color_from_hex('#e6461faa')
        c3 = get_color_from_hex('#81cac8aa')
        c4 = get_color_from_hex('#7f398baa')

        cx, cy = Window.center
        m = 50
        m2 = m * 2
        with self.canvas:
            self.c1 = Color(*c1)
            BorderImage(texture=btnbg, pos=(m, m), size=(cx - m2, cy - m2))
            self.c2 = Color(*c2)
            BorderImage(texture=btnbg, pos=(cx + m, m), size=(cx - m2, cy - m2))
            self.c3 = Color(*c3)
            BorderImage(texture=btnbg, pos=(m, cy + m), size=(cx - m2, cy - m2))
            self.c4 = Color(*c4)
            BorderImage(texture=btnbg, pos=(cx + m, cy + m), size=(cx - m2, cy - m2))

class Choose(KalScenarioServer):
    resources = (
        'background.png',
        'client.py',
        'buttonbackground.png'
    )

    def __init__(self, *largs):
        super(Choose, self).__init__(*largs)
        self.players = {}
        self.selected_scenario = None
        self.view = ChooseView()
        self.controler.app.show(self.view)
        Clock.schedule_interval(self._update_color, 1 / 30.)

    def _update_color(self, dt):
        places = [player['place'] for player in self.players.itervalues()]
        delta = abs(cos(Clock.get_time() * 3)) * 0.4
        if 1 in places:
            self.view.c1.a = 0.55 + delta
        if 2 in places:
            self.view.c2.a = 0.55 + delta
        if 3 in places:
            self.view.c3.a = 0.55 + delta
        if 4 in places:
            self.view.c4.a = 0.55 + delta

    def start(self):
        super(Choose, self).start()
        self.players = {}
        self.state = 'waitready'
        self.scenario = None
        self.send_remaining_places()

    def client_login(self, client):
        self.players[client] = {
            'place': -1,
            'ready': False,
        }
        self.send_remaining_places()

    def client_logout(self, client):
        del self.players[client]
        self.send_remaining_places()
        self.send_wait()

    def reset(self):
        for infos in self.players.itervalues():
            infos['place'] = -1
            infos['ready'] = False

    def send_remaining_places(self):
        places = range(1, 5)
        for player in self.players.itervalues():
            place = player['place']
            if place in places:
                places.remove(place)
        for client, infos in self.players.iteritems():
            if infos['place'] >= 0:
                continue
            self.send_to(client, 'PLACE %s' % ' '.join(map(str, places)))

    def send_wait(self):
        ready = len([x for x, z in self.players.iteritems() if z['ready'] and
                     z['place'] != -1])
        total = len([x for x, z in self.players.iteritems() if z['place'] != -1])

        print 'send_wait', ready, total

        if total < MIN_PLAYERS:
            msg = 'Il manque un joueur pour commencer'
            self.reset()
            self.send_remaining_places()
        else:
            msg = 'Il reste %d joueur%s en cours de connexion' % (
                total - ready, '' if ready <= 1 else 's')

        for client, infos in self.players.iteritems():
            if infos['ready'] is True:
                self.send_to(client, 'WAIT %s' % msg)

    #
    # Server command
    #
    def handle_connect(self, client):
        self.send_remaining_places()


    #
    # Client command
    #
    def do_client_place(self, client, args):
        # a client just ask for a place.
        # is the place is available ?
        place = args[0]
        self.players[client]['place'] = int(place)
        self.controler.metadata[client] = {'place': int(place)}
        self.send_remaining_places()
        if self.selected_scenario is None:
            self.send_to(client, 'SCENARIO')
        else:
            self.send_to(client, 'BEREADY')

    def do_client_scenario(self, client, args):
        # a client ask for a specific scenario
        self.selected_scenario = args[0]
        self.send_to(client, 'BEREADY')
        for client, player in self.players.iteritems():
            if player['place'] != -1:
                self.send_to(client, 'BEREADY')

    def do_client_ready(self, client, args):
        self.players[client]['ready'] = True
        self.send_wait()


    #
    # State machine
    #
    def run_waitready(self):
        if self.controler.waitclients:
            for client in self.controler.waitclients:
                self.controler.clients[client] = self.controler.waitclients[client]
                self.controler.load(client)
            self.controler.waitclients = {}
        if len(self.players) < 1:
            return
        ready = 0
        total = len([x for x, z in self.players.iteritems() if z['place'] != -1])
        for client, infos in self.players.iteritems():
            if infos['place'] == -1:
                continue
            if infos['ready']:
                ready += 1
        if ready < MIN_PLAYERS or ready != total:
            return
        print 'SWITCH TO LAUNCH ???'
        self.state = 'launch'

    def run_launch(self):
        print '======== RUN LAUNCH'
        for client in self.players.keys()[:]:
            infos = self.players[client]
            if infos['place'] == -1:
                self.client_logout(client)
                self.controler.reset(client)

        self.controler.switch_scenario(self.selected_scenario)
        for client in self.players.keys()[:]:
            infos = self.players[client]
            if infos['place'] == -1:
                continue
            self.controler.load(client)

scenario_class = Choose
