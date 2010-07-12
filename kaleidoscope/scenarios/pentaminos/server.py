from kaleidoscope.scenario import KalScenarioServer
from time import time
from random import randint

PENTAMINOS_SIZE = 5, 3
PENTAMINOS_COUNT_BY_USERS = 3
PENTAMINOS_COLORS = (
    ('#86aa21', '#ffffff'),
    ('#3690ca', '#ffffff'),
    ('#e8d337', '#ffffff'),
    ('#cc3a6e', '#ffffff')
) * 10

class Pentaminos(KalScenarioServer):
    def __init__(self, *largs):
        super(Pentaminos, self).__init__(*largs)
        self.timeout = 0
        self.state = 'idle'
        self.players = {}
        idx = 0

        # init client table
        for client in self.controler.clients:
            self.players[client] = {
                'client': client,
                'color': PENTAMINOS_COLORS[idx],
                'name': self.controler.get_client_name(client),
                'pentaminos': []
            }
            idx += 1

    def client_receive(self, client, args):
        c = args.split()
        if len(c) == 0:
            return
        cmd = c[0].lower()
        if cmd == 'pentamino':
            if len(c) != 5:
                self.send_to(client, 'ERROR invalid command\n')
                return
            key, w, h, penta = c[1:]
            w, h = map(int, (w, h))
            print '# Add pentamino %s from %s to the list' % (key, client.addr)
            self.players[client]['pentaminos'].append((key, w, h, penta))
            left = PENTAMINOS_COUNT_BY_USERS - len(self.players[client]['pentaminos'])
            if left:
                # validate to client
                self.send_to(client, 'CLEAR')
                self.send_to(client, 'GIVE 5')
                self.send_to(client, 'MSG Great job, you have %d pentaminos left to do' % left)
            else:
                self.send_to(client, 'CLEAR')
                self.send_to(client, 'MSG You\'ve finished ! Please wait other people now :)')

    def send_to(self, client, message):
        self.controler.send_to(client, 'GAME %s\n' % message)

    def send_all(self, message):
        self.controler.send_all('GAME %s\n' % message)

    def msg_all(self, message):
        self.send_all('MSG %s' % message)

    def start(self):
        super(Pentaminos, self).start()
        self.msg_all('You must do %d pentaminos' % PENTAMINOS_COUNT_BY_USERS)
        # XXX don't change order, i known, it suck.
        for client, player in self.players.iteritems():
            self.send_to(client, 'COLOR %s %s' % player['color'])
        self.send_all('SIZE %d %d' % PENTAMINOS_SIZE)
        self.send_all('START')
        self.send_all('GIVE 5')
        self.state = 'game1'
        self.pentaminos = []

    def run(self):
        super(Pentaminos, self).run()
        getattr(self, 'run_%s' % self.state)()

    def run_idle(self):
        pass

    def run_game1(self):
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

        # distribute
        for player in self.players.itervalues():
            for penta in player['pentaminos']:
                # send the penta to the user
                self.send_all('PENTA %s %d %d %s %s %s' % (
                    penta[0], penta[1], penta[2], penta[3],
                    player['name'], player['color'][0]))

        # reset background to white
        self.send_all('COLOR #ffffff #000000')

    def run_game2(self):
        pass

scenario_class = Pentaminos
