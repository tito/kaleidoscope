from os.path import dirname, join, realpath
from os import walk
from kaleidoscope.scenario import KalScenarioServer
from time import time

from kivy.core.image import Image
from kivy.uix.floatlayout import FloatLayout
from fresco_common import Fresco, FrescoThumbnail
from random import randint
from kivy.resources import resource_add_path, resource_remove_path
from kivy.lang import Builder

TIMER_1 = 120
TIMER_2 = 30
MAX_CLIENT_ITEMS = 3

background = Image(join(dirname(__file__), 'background.png'))
background.texture.wrap = 'repeat'
btnbg = Image(join(dirname(__file__), 'buttonbackground.png')).texture

# vert, jaune, bleu, rose
fresco_colors = (
    (92, 179, 103),
    (194, 222, 65),
    (92, 145, 179),
    (227, 53, 119),
)
fresco_logos = (
    'umbrella',
    'horse',
    'plane',
    'ying',
)

class FrescoServerLayout(FloatLayout):
    pass

from kivy.factory import Factory
Factory.register('FrescoServerLayout', cls=FrescoServerLayout)


class FrescoServer(KalScenarioServer):
    def search_data_files(self):
        blacklist = ('__init__.py', )
        curdir = realpath(dirname(__file__))
        for root, dirnames, filenames in walk(dirname(__file__)):
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                if filename in blacklist:
                    continue
                filename = join(root, filename)
                filename = realpath(filename)
                if filename.startswith(curdir):
                    filename = filename[len(curdir):]
                if filename.startswith('/'):
                    filename = filename[1:]
                yield filename

    def __init__(self, *largs):
        self.resources = list(self.search_data_files())
        resource_add_path(dirname(__file__))
        Builder.load_file(join(dirname(__file__), 'fresco.kv'))

        super(FrescoServer, self).__init__(*largs)
        self.timeout = 0
        self.timemsg = 0
        self.players = {}

        # init client table
        for client in self.controler.clients:
            self.players[client] = {
                'client': client,
                'name': self.controler.get_client_name(client),
                'ready': False,
                'done': False,
                'place': self.controler.metadata[client]['place'],
                'count': 0
            }

    def client_login(self, client):
        self.players[client]['ready'] = True

    def client_logout(self, client):
        del self.players[client]

    def start(self):
        '''Scenario start, wait for all player to be ready
        '''
        super(FrescoServer, self).start()
        self.send_all('WAITREADY')
        self.state = 'waitready'

    def stop(self):
        Builder.unload_file(join(dirname(__file__), 'fresco.kv'))
        resource_remove_path(dirname(__file__))

    def init_ui(self):
        self.layout = FrescoServerLayout()
        self.fresco = Fresco(server=True, size_hint=(.8, .8),
                pos_hint={'x': .1, 'y': .1})
        self.layout.add_widget(self.fresco)
        self.controler.app.show(self.layout)

    #
    # Client commands received
    # do_client_<command>(client, [...])
    #

    def do_client_ready(self, client, args):
        self.players[client]['ready'] = True
        count = len([x for x in self.players.itervalues() if not x['ready']])
        if count:
            self.msg_all('@%s ok, en attente de %d joueur(s)' % (
                self.players[client]['name'], count))

    def do_client_pos(self, client, args):
        index = int(args[0])
        date = float(args[1])
        thumb = None
        for child in self.layout.children:
            if not isinstance(child, FrescoThumbnail):
                continue
            if child.index != index:
                continue
            thumb = child
            break
        if thumb is None:
            thumb = self.fresco.get_thumb(index)
            thumb.client = client
            place = int(self.players[client]['place']) - 1
            thumb.color = map(lambda x: x / 255., fresco_colors[place])
        if date == -1:
            if thumb.parent is not None:
                thumb.parent.remove_widget(thumb)
        else:
            if thumb.parent is None:
                self.layout.add_widget(thumb, -1)
            alpha = self.fresco.get_alpha_from_realdate(date)
            self.fresco.set_date_by_alpha(thumb, alpha)
            self.fresco.set_pos_by_alpha(thumb, alpha)

    #
    # State machine
    #

    def run_waitready(self):
        '''Wait for all player to be ready
        '''
        ready = True
        for player in self.players.itervalues():
            ready = ready and player['ready']
        if not ready:
            return

        self.timeout = time() + TIMER_1
        self.send_all('GAME1')
        self.send_all('TIME %d %d' % (time(), int(self.timeout)))
        self.state = 'game1'
        self.init_ui()
        self.items_given = []

        for client in self.controler.clients:
            place = int(self.players[client]['place']) - 1
            self.send_to(client, 'COLOR %d %d %d' % fresco_colors[place])
            self.send_to(client, 'LOGO %s' % fresco_logos[place])

        # deliver randomly index
        litems = len(self.fresco.data)
        if litems:
            r = range(litems)
            allfinished = False
            while not allfinished:
                allfinished = True
                for client in self.controler.clients:
                    player = self.players[client]
                    if player['ready'] is False:
                        continue
                    if player['count'] > MAX_CLIENT_ITEMS - 1:
                        continue
                    index = r.pop(randint(0, litems - 1))
                    litems -= 1
                    self.send_to(client, 'GIVE %d' % index)
                    allfinished = allfinished and False
                    player['count'] += 1
                    self.items_given.append((client, index))

    def run_game1(self):
        '''First game, place items on the fresco without ordering.
        '''
        if time() > self.timeout:
            self.state = 'reset_for_game2'
            return

    def run_reset_for_game2(self):
        '''Order fresco !
        '''
        self.send_all('GAME2')

        # order !
        index_sent = []
        for thumb in self.layout.children:
            if not isinstance(thumb, FrescoThumbnail):
                continue

            # are we far from now ?
            realdate = thumb.item['date']
            now = thumb.date
            diff = abs(realdate - now)
            if diff > self.fresco.date_allowed_offset:
                self.send_to(thumb.client, 'THNOTVALID %d' % thumb.index)
            else:
                self.send_to(thumb.client, 'THVALID %d' % thumb.index)
            index_sent.append(thumb.index)

        for client, index in self.items_given:
            if index in index_sent:
                continue
            self.send_to(client, 'THNOTVALID %d' % index)

        # do game 2
        self.timeout = time() + TIMER_2
        self.send_all('TIME %d %d' % (time(), int(self.timeout)))
        self.state = 'game2'

    def run_game2(self):
        if time() > self.timeout:
            self.state = 'reset_for_game3'
            return

    def run_reset_for_game3(self):
        for client, index in self.items_given:
            self.send_to(client, 'THVALID %d' % index)
        self.state = 'game3'
        self.timeout = time() + 15
        self.send_all('TIME %d %d' % (time(), int(self.timeout)))

    def run_game3(self):
        if time() > self.timeout:
            self.controler.switch_scenario('choose')
            self.controler.load_all()

scenario_class = FrescoServer
