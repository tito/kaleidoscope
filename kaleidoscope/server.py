'''
Kaleidoscope - Server
'''

import kivy
kivy.require('1.0.6')

import sys
import traceback
import asyncore, asynchat
import socket
import base64

from kaleidoscope import config

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty
from kivy.resources import resource_add_path
from os.path import dirname

resource_add_path(dirname(__file__))

class KalControler(object):
    '''Network controler.
    '''
    _instance = None

    @staticmethod
    def instance():
        if KalControler._instance is None:
            KalControler._instance = KalControler()
        return KalControler._instance

    def __init__(self):
        super(KalControler, self).__init__()
        self.running = False
        self.state = 'idle'
        self.clientcount = 0
        self.metadata = {}
        self.clients = {}
        self.waitclients = {}
        self.reset_game()

    def reset_game(self):
        self.scenarioname = 'choose'
        self.scenario = None
        self.status = {}

    #
    # Send message to a specific client
    #

    def get_client_name(self, client):
        return self.clients[client]

    def reset(self, client):
        self.waitclients[client] = self.clients[client]
        del self.clients[client]
        self.raw(client, 'RESET\n')

    def raw(self, client, message):
        '''Send a raw message
        '''
        try:
            #print '<', client.addr, message.replace('\n', '')
            client.push(message)
        except:
            print '# Fatal error while sending %s to %s' % (message, client)

    def failed(self, client, message):
        '''Return a error message to the client
        '''
        self.raw(client, 'FAILED %s\n' % message)

    def ok(self, client, message=None):
        '''Return a ok message to the client
        '''
        if message:
            self.raw(client, 'OK %s\n' % message)
        return self.raw(client, 'OK\n')

    def send_to(self, client, message):
        self.raw(client, message)

    #
    # Global clients commands
    #

    def send_all(self, message, client=None):
        for cli in self.clients:
            if client and cli is client:
                continue
            self.raw(cli, message)

    def notify_all(self, message, client=None):
        self.send_all('NOTIFY %s\n' % message, client)

    #
    # Handle network command
    #

    def handle_from(self, client, cmd, args):
        '''Handle a command from a client + ensure that the client is known.
        '''
        if client not in self.clients and self.running:
            return self.failed(client, 'A game is running')

        try:
            func = getattr(self, 'command_%s' % cmd.lower())
            func(client, args)
        except Exception, e:
            self.failed(client, 'Invalid command <%s>' % cmd.lower())
            traceback.print_exc()

    def command_login(self, client, args):
        '''Subscribe to the game, if possible.
        '''
        if client in self.clients:
            return self.failed(client, 'Inscription invalide')
        if len(args) <= 2:
            return self.failed(client, 'Login invalide')
        self.waitclients[client] = args
        self.notify_all('@%s est en ligne' % args)
        self.ok(client)
        self.send_to(client, 'NOTIFY Attente d\'acceptation...\n')

    def command_logout(self, client, args):
        '''Logout of the current game
        '''
        if client in self.clients:
            clientname = self.clients[client]
            del self.clients[client]
            self.notify_all('@%s est parti' % clientname)
            if self.scenario:
                self.scenario.client_logout(client)
        elif client in self.waitclients:
            del self.waitclients[client]

    def command_status(self, client, args):
        '''Update the current status of the client
        '''
        self.status[client] = args.lower()

    def command_game(self, client, args):
        '''Receive a Game command, send back to the current scenario
        '''
        if self.scenario is not None:
            self.scenario.client_receive(client, args)

    def command_get(self, client, args):
        '''The client ask for a specific file of the scenario, get it.
        '''
        scenarioname, filename = args.split()
        if scenarioname != self.scenarioname:
            self.failed(client, 'Invalid scenario name for GET')
            return
        data = self.scenario.get(filename)
        data = base64.urlsafe_b64encode(data)
        cmd = 'WRITE %s %s %s\n' % (scenarioname, filename, data)
        self.send_to(client, cmd)

    #
    # Scenario handling state machine
    #

    def tick_state_machine(self):
        '''State machine of the game, call the appropriate state
        '''
        # ensure the game can go, if they are at least one client.
        if len(self.clients) + len(self.waitclients) == 0:
            if self.state != 'idle':
                print '# All clients have leaved, reset to idle.'
                self.state = 'idle'
                # XXX FIXME
                self.app.show()
                self.reset_game()

        try:
            funcname = 'state_%s' % self.state
            getattr(self, funcname)()
        except Exception, e:
            print 'KalControler error at', funcname
            print e

    def switch_scenario(self, scenario):
        print '# Switch to', scenario
        self.scenarioname = scenario
        self.state_load()

    def load_all(self):
        for client in self.clients:
            self.load(client)

    def load(self, client):
        if client in self.status:
            del self.status[client]
        if self.state == 'idle':
            self.state_load()
        try:
            self.send_to(client, 'LOAD %s\n' % self.scenarioname)
            for x in self.scenario.resources:
                self.send_to(client, 'REQUIRE %s %s %s\n' % (
                    self.scenarioname, x, self.scenario.sha224(x)))
        except Exception, e:
            self.notify_all('Server error while trying to load scenario', client)
            self.notify_all('Game cancelled.', client)
            traceback.print_exc()
            return

    def state_idle(self):
        '''Default handler when nothing is done.
        Just wait for few peoples to come in the game.
        '''
        l = len(self.clients) + len(self.waitclients)
        if l <= 0:
            return
        self.state = 'load'
        self.clientcount = l

    def state_load(self):
        try:
            package = 'kaleidoscope.scenarios.%s' % self.scenarioname
            for x in sys.modules.keys()[:]:
                if x.startswith(package):
                    del sys.modules[x]

            pack = __import__(package, fromlist=['server'])
            self.scenario = pack.server.scenario_class(self)
        except Exception, e:
            self.notify_all('Server error while trying to load scenario')
            self.notify_all('Game cancelled.')
            self.state = 'idle'
            traceback.print_exc()
            return
        self.state = 'running'

    def state_running(self):
        if self.scenarioname != 'choose' and \
           not self.clients and \
           self.waitclients:
            self.scenarioname = 'choose'
            self.state = 'idle'
            return

        # Sync part
        name = self.get_client_name
        for client in self.clients:
            issync = True
            if client not in self.status:
                print '# Waiting status of @%s' % name(client)
                self.send_to(client, 'SYNC %s\n' % self.scenarioname)
                self.status[client] = '__init__'
                continue

            status = self.status[client]
            if status == 'done':
                continue
            elif status == 'wait requirement':
                self.send_to(client, 'SYNC %s\n' % self.scenarioname)
            elif status == 'ready':
                self.status[client] = 'done'
                self.scenario.client_login(client)
            else:
                print '# @%s is still %s' % (name(client), status)

        # Scenario part
        try:
            self.scenario.update()
        except:
            traceback.print_exc()

class KalServerChannel(asynchat.async_chat):

    def __init__(self, server, sock, addr):
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator("\n")
        self.request = None
        self.data = ''
        self.shutdown = 0

    def collect_incoming_data(self, data):
        self.data = self.data + data

    def found_terminator(self):
        out = self.data.split(None, 1)
        if len(out) == 0:
            return
        if len(out) == 2:
            cmd, args = out
        else:
            cmd = out[0]
            args = []
        self.dispatch_command(cmd, args)
        self.data = ''

    def dispatch_command(self, cmd, args):
        #print '>', self.addr, cmd, args
        KalControler.instance().handle_from(self, cmd, args)

    def handle_close(self):
        print '# Client disconnected', self.addr
        self.dispatch_command('LOGOUT', ())
        return asynchat.async_chat.handle_close(self)

class KalServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(4)

    def handle_accept(self):
        conn, addr = self.accept()
        print '# Client connected', addr
        KalServerChannel(self, conn, addr)

class KalServerScreenWait(FloatLayout):
    time = NumericProperty(0)

    def __init__(self, **kwargs):
        super(KalServerScreenWait, self).__init__(**kwargs)
        Clock.schedule_interval(self.increase_time, 1 / 30.)

    def increase_time(self, dt):
        self.time += dt

class KalServerApp(App):

    def build(self):
        print '# Create Controler'
        self.controler = KalControler.instance()
        self.controler.app = self
        print '# Start Kaleidoscope server at', (config.server_ip, config.server_port)
        self.server = KalServer(config.server_ip, config.server_port)
        Clock.schedule_interval(self.update_loop, 0)

        self.root = FloatLayout()
        self.screen_wait = KalServerScreenWait()
        self.root.add_widget(self.screen_wait)
        return self.root

    def update_loop(self, *l):
        asyncore.loop(timeout=0, count=10)
        KalControler.instance().tick_state_machine()

    def show(self, widget=None):
        self.root.clear_widgets()
        if widget:
            self.root.add_widget(widget)
        else:
            self.root.add_widget(self.screen_wait)
