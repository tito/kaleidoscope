'''
Kaleidoscope - Server
'''

from kaleidoscope import config
import asyncore, asynchat
import os, socket, string
from time import time

class KalGameControler(object):
    def __init__(self, controler):
        self.controler = controler
        self.running = False
        self.state = 'idle'
        self.countdown = time()
        self.lastcountdown = 0
        self.scenarioname = 'pentaminos'
        self.clientcount = 0
        self.status = {}
        self.scenario = None

    def tick(self):
        '''State machine of the game, call the appropriate state
        '''

        # ensure the game can go, if they are at least one client.
        if len(self.controler.clients) == 0:
            if self.state != 'idle':
                print '# All clients have leaved, reset to idle.'
                self.state = 'idle'

        try:
            funcname = 'handle_%s' % self.state
            getattr(self, funcname)()
        except Exception, e:
            print 'KalGameControler error at', funcname
            print e

    def update_client_status(self, client, status):
        '''Update status of a client
        '''
        self.status[client] = status.lower()

    def client_receive(self, client, args):
        '''Send data from client to game
        '''
        self.scenario.client_receive(client, args)

    def handle_idle(self):
        '''Default handler when nothing is done.
        Just wait for few peoples to come in the game.
        '''
        l = len(self.controler.clients)
        if l <= 0:
            return
        self.countdown = time() + config.countdown
        self.state = 'waiting'
        self.clientcount = l

    def handle_waiting(self):
        l = len(self.controler.clients)
        if l != self.clientcount:
            self.controler.notify_all('Start canceled, new player is coming.')
            self.state = 'idle'
            return
        left = int(self.countdown - time())
        if self.lastcountdown != left:
            self.controler.notify_all('Game will start in %ds' % left)
            self.lastcountdown = left
        if left <= 0:
            self.state = 'scnload'

    def handle_scnload(self):
        # load the scenario
        try:
            pack = __import__('kaleidoscope.scenarios.%s' % self.scenarioname, fromlist=['server'])
            self.scenario = pack.server.scenario_class(self)
            self.controler.send_all('SCNLOAD %s\n' % self.scenarioname)
        except Exception, e:
            self.controler.notify_all('Server error while trying to load scenario')
            self.controler.notify_all('Game cancelled.')
            self.state = 'idle'
            import traceback
            traceback.print_exc()
            return
        self.state = 'scnwait'

    def handle_scnwait(self):
        name = self.controler.get_client_name
        allsync = True
        for cli in self.controler.clients:
            if cli not in self.status:
                print '# Waiting status of @%s' % name(cli)
                allsync = False
                continue
            status = self.status[cli]
            if status != 'ok':
                print '# @%s is still %s' % (name(cli), status)
                allsync = False
                continue
        if allsync:
            print '# Starting !'
            self.state = 'running'

    def handle_running(self):
        try:
            self.scenario.update()
        except:
            import traceback
            traceback.print_exc()


class KalControler(object):
    instance = None

    @staticmethod
    def get_instance():
        if KalControler.instance is None:
            KalControler.instance = KalControler()
        return KalControler.instance

    def __init__(self):
        super(KalControler, self).__init__()
        self.clients = {}
        self.game = KalGameControler(self)

    def get_client_name(self, client):
        return self.clients[client]

    def tick(self):
        '''State machine of the game :)
        '''
        self.game.tick()

    def raw(self, client, message):
        '''Send a raw message
        '''
        try:
            print '<', client.addr, message.replace('\n', '')
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

    def send_all(self, message, client=None):
        for cli in self.clients:
            if client and cli is client:
                continue
            self.raw(cli, message)

    def notify_all(self, message, client=None):
        self.send_all('NOTIFY %s\n' % message, client)

    def handle_from(self, client, cmd, args):
        '''Handle a command from a client + ensure that the client is known.
        '''
        if client not in self.clients and self.game.running:
            return self.failed(client, 'A game is running')

        try:
            func = getattr(self, 'handle_%s' % cmd.lower())
            func(client, args)
        except Exception, e:
            self.failed(client, 'Invalid command <%s>' % cmd.lower())

    def handle_login(self, client, args):
        '''Subscribe to the game, if possible.
        '''
        if client in self.clients:
            return self.failed(client, 'Already subscribed')
        if len(args) <= 2:
            return self.failed(client, 'Invalid login')
        self.clients[client] = args
        self.notify_all('@%s joined the game' % args)
        self.ok(client)

    def handle_logout(self, client, args):
        if client not in self.clients:
            return
        del self.clients[client]
        self.notify_all('@%s leave the game' % args)

    def handle_status(self, client, args):
        self.game.update_client_status(client, args)

    def handle_game(self, client, args):
        self.game.client_receive(client, args)


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
        print '>', self.addr, cmd, args
        KalControler.get_instance().handle_from(self, cmd, args)

    def handle_close(self):
        print '# Client disconnected', self.addr
        self.dispatch_command('LOGOUT', ())
        return asynchat.async_chat.handle_close(self)

class KalServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.listen(4)

    def handle_accept(self):
        conn, addr = self.accept()
        print '# Client connected', addr
        KalServerChannel(self, conn, addr)

if __name__ == '__main__':
    from kaleidoscope import config

    print '# Start Kaleidoscope server at', (config.server_ip, config.server_port)
    s = KalServer(config.server_ip, config.server_port)
    try:
        while True:
            asyncore.loop(timeout=.05, count=1)
            KalControler.get_instance().tick()
    except:
        print '# Close the socket...'
        s.close()
        raise
