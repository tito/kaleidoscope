from kaleidoscope.scenario import KalScenarioServer
from time import time
from random import randint
from penta_color import penta_schemes

PENTAMINOS_SIZE = 5, 3
PENTAMINOS_SIZE2 = 6, 5
PENTAMINOS_COUNT_BY_USERS = 3

class Pentaminos(KalScenarioServer):
    resources = (
        'client.py',
        'myriad.ttf',
        'penta_color.py',
    )
    def __init__(self, *largs):
        super(Pentaminos, self).__init__(*largs)
        self.timeout = 0
        self.players = {}
        idx = 0

        # init client table
        for client in self.controler.clients:
            self.players[client] = {
                'client': client,
                'name': self.controler.get_client_name(client),
                'ready': False,
                'pentaminos': []
            }
            idx += 1

    def start(self):
        '''Scenario start, wait for all player to be ready
        '''
        super(Pentaminos, self).start()
        self.send_all('BEREADY')
        self.state = 'waitready'

    #
    # Client commands received
    # do_client_<command>(client, [...])
    #

    def do_client_pentamino(self, client, args):
        if len(args) != 4:
            self.send_to(client, 'ERROR invalid command\n')
            return
        key, w, h, penta = args
        w, h = map(int, (w, h))
        print '# Add pentamino %s from %s to the list' % (key, client.addr)
        self.players[client]['pentaminos'].append((key, w, h, penta))
        left = PENTAMINOS_COUNT_BY_USERS - len(self.players[client]['pentaminos'])
        if left:
            # validate to client
            self.send_to(client, 'GIVE 5')
            self.send_to(client, 'MSG Great job, you have %d pentaminos left to do' % left)
        else:
            self.send_to(client, 'MSG You\'ve finished ! Please wait other people now :)')

    def do_client_ready(self, client, args):
        self.players[client]['ready'] = True
        count = len([x for x in self.players.itervalues() if not x['ready']])
        if count:
            self.msg_all('@%s is ready, waiting %d players' % (
                self.players[client]['name'], count))

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

        self.msg_all('You must do %d pentaminos' % PENTAMINOS_COUNT_BY_USERS)
        self.send_all('SIZE %d %d' % PENTAMINOS_SIZE)
        self.send_all('GAME1')
        self.send_all('GIVE 5')
        self.state = 'game1'
        self.pentaminos = []

    def run_game1(self):
        '''Game is running
        '''
        done = True
        for player in self.players.itervalues():
            if len(player['pentaminos']) != PENTAMINOS_COUNT_BY_USERS:
                done = False
        if done:
            print '# All users have finished game1'
            self.state = 'reset_for_game2'

    def run_reset_for_game2(self):
        self.send_all('CLEAR')
        self.msg_all('Well done ! Now, construct a rect :)')
        self.state = 'game2'

        # extract all pentaminos
        pentas = []
        for player in self.players.itervalues():
            for penta in player['pentaminos']:
                pentas.append((penta, player))

        # do game 2
        self.send_all('GAME2')
        self.send_all('SIZE %d %d' % PENTAMINOS_SIZE2)

        # distribute
        for player in self.players.itervalues():
            for k, v in penta_schemes.iteritems():
                size, string = v[0]
                w, h = size
                # send the penta to the user
                self.send_all('PENTA %s %d %d %s' % (
                    k, w, h, string))

    def run_game2(self):
        pass

scenario_class = Pentaminos
