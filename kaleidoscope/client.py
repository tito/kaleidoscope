import time
import asyncore, asynchat
import socket
from pymt import *

class KalClientChannel(asynchat.async_chat):
    def __init__(self, server, sock, addr, ui):
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator("\n")
        self.request = None
        self.data = ''
        self.shutdown = 0
        self.scenario = None
        self.scenarioname = ''
        self.ui = ui

    def collect_incoming_data(self, data):
        self.data = self.data + data

    def login(self, nickname):
        self.push('LOGIN %s\n' % nickname)

    def found_terminator(self):
        out = self.data.split(None, 1)
        self.data = ''
        if len(out) == 0:
            return
        if len(out) == 2:
            cmd, args = out
        else:
            cmd = out[0]
            args = []
        self.dispatch_command(cmd, args)

    def dispatch_command(self, cmd, args):
        try:
            func = getattr(self, 'handle_%s' % cmd.lower())
            func(args)
        except Exception, e:
            print e
            #self.failed(client, 'Invalid command <%s>' % cmd.lower())

    def handle_ok(self, args):
        self.ui.dispatch_event('on_ok', args)

    def handle_failed(self, args):
        self.ui.dispatch_event('on_failed', args)

    def handle_notify(self, args):
        self.ui.dispatch_event('on_notify', args)

    def handle_scnload(self, args):
        self.ui.dispatch_event('on_scnload', args)
        self.push('STATUS loading\n')
        try:
            self.scenarioname = args
            pack = __import__('kaleidoscope.scenarios.%s' % self.scenarioname,
                              fromlist=['client'])
            self.scenario = pack.client.scenario_class(self)
        except Exception, e:
            self.push('STATUS failed <%s>\n' % e)
            raise
        self.push('STATUS ok\n')

    def handle_game(self, args):
        self.scenario.update_server(args)

    def handle_error(self):
        print '<<<<<<<<<<<<<<<<<<<<<< ERROR'
    def log(self, message):
        print '<<<<<<<<<<<<<<<<<<<<<!!', message

class KalClient(asyncore.dispatcher):

    def __init__(self, host, port, ui):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect( (host, port) )
        self.channel = None
        self.ui = ui

    def handle_connect(self):
        self.channel = KalClientChannel(self, self.socket, self.addr, self.ui)

class KalClientInteractive(MTWidget):
    def __init__(self, **kwargs):
        super(KalClientInteractive, self).__init__(**kwargs)
        self.nickname = kwargs.get('nickname', 'jubei')
        self.ip = kwargs.get('ip', '127.0.0.1');
        self.port = kwargs.get('port', 6464)
        self.container = MTWidget(size=self.size)
        self.add_widget(self.container)

        self.register_event_type('on_ok')
        self.register_event_type('on_failed')
        self.register_event_type('on_notify')
        self.register_event_type('on_scnload')

        self.client = KalClient(self.ip, self.port, self)
        self.logged = False
        self.history = []

        getClock().schedule_interval(self.update_loop, 0)
        self.dispatch_event('on_notify', 'Connecting to %s' % self.ip)

    def update_loop(self, *l):
        asyncore.loop(timeout=0, count=1)
        if self.client.channel is None:
            return
        if not self.logged:
            self.client.channel.login(self.nickname)
            self.logged = True

    def on_ok(self, args):
        pass

    def on_failed(self, args):
        pass

    def on_notify(self, args):
        self.history.append(args)
        if len(self.history) > 4:
            self.history = self.history[1:]
        pymt_logger.info('Kal: %s' % args)

    def on_scnload(self, args):
        pass

    def draw(self):
        # if we have a scenario, draw it
        if self.client.channel:
            if self.client.channel.scenario is not None:
                self.client.channel.scenario.draw()
                return

        # draw our background so
        if len(self.history):
            label = self.history[-1]
            drawLabel(label=label, pos=self.center,
                      font_size=42, color=(1, 1, 1, 1))
