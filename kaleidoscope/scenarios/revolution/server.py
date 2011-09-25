from os.path import dirname, join, realpath
from os import walk
from kaleidoscope.scenario import KalScenarioServer
from time import time

from kivy.core.image import Image
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.graphics import Color, BorderImage
from kivy.uix.floatlayout import FloatLayout
from fresco_common import Fresco, FrescoThumbnail
from random import randint
from kivy.resources import resource_add_path
from kivy.lang import Builder

TIMER = 60 * 2
MAX_CLIENT_ITEMS = 3

background = Image(join(dirname(__file__), 'background.png'))
background.texture.wrap = 'repeat'
btnbg = Image(join(dirname(__file__), 'buttonbackground.png')).texture

fresco_colors = ((227, 53, 119), (92, 145, 179), (92, 179, 103), (194, 222, 65))
fresco_logos = ('ying', 'plane', 'umbrella', 'horse')


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

    def init_ui(self):
        self.layout = FloatLayout()
        self.fresco = Fresco(server=True)
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
        index, date = map(int, args)
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
        if date == -1:
            if thumb.parent is not None:
                print 'REMOVE THUMB'
                thumb.parent.remove_widget(thumb)
        else:
            if thumb.parent is None:
                print 'ADD THUMB'
                self.layout.add_widget(thumb)
            self.fresco.set_pos_by_date(thumb, date)
        print thumb.item['title'], thumb.pos, thumb.size

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

        self.timeout = time() + TIMER
        self.send_all('GAME1')
        self.send_all('TIME %d %d' % (time(), int(self.timeout)))
        self.state = 'game1'
        self.init_ui()

        for client in self.controler.clients:
            place = int(self.players[client]['place']) - 1
            self.send_to(client, 'COLOR %d %d %d' % fresco_colors[place])
            self.send_to(client, 'LOGO %s' % fresco_logos[place])

        # deliver randomly index
        litems = len(self.fresco.data)
        if litems:
            r = range(litems)
            print 'range of', r
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

    def run_game1(self):
        '''First game, place items on the fresco without ordering.
        '''
        if time() > self.timeout:
            self.state = 'reset_for_game2'
            return

    def run_reset_for_game2(self):
        '''Order fresco !
        '''
        # do game 2
        self.send_all('ORDER')
        self.timeout = time() + TIMER
        self.send_all('TIME %d %d' % (time(), int(self.timeout)))

    def run_game2(self):
        if time() > self.timeout:
            self.msg_all('Fin du jeu !')
            self.state = 'game3'
            self.timeout = time() + 5
            self.send_all('TIME %d %d' % (time(), int(self.timeout)))
            return

    def run_game3(self):
        if time() > self.timeout:
            self.controler.switch_scenario('choose')
            self.controler.load_all()

scenario_class = FrescoServer
