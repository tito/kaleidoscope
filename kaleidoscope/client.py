import asyncore
import asynchat
import socket
import os
import errno
import hashlib
import base64
import traceback

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.logger import Logger
from kivy.clock import Clock

class KalCache(object):
    directory = os.path.join(os.path.dirname(__file__), 'cache')

    @staticmethod
    def create(directory):
        try:
            os.makedirs(directory)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                pass
            else:
                raise

        filename = os.path.join(directory, '__init__.py')
        if not os.path.exists(filename):
            with open(filename, 'w') as fd:
                fd.write('')

    @staticmethod
    def init():
        KalCache.create(KalCache.directory)

    @staticmethod
    def initscenario(scenarioname):
        directory = os.path.join(KalCache.directory, scenarioname)
        KalCache.create(directory)

    @staticmethod
    def validate(scenarioname, resource, sha):
        filename = os.path.join(KalCache.directory, scenarioname, resource)
        if not os.path.exists(filename):
            return False
        with open(filename, 'rb') as fd:
            hash = hashlib.sha224(fd.read()).hexdigest()
        return sha == hash

    @staticmethod
    def write(scenarioname, resource, data):
        filename = os.path.join(KalCache.directory, scenarioname, resource)
        KalCache.initscenario(scenarioname)

        with open(filename, 'wb') as fd:
            fd.write(data)

class KalClientChannel(asynchat.async_chat):
    def __init__(self, server, sock, addr, ui):
        self.server = server
        self.addr = addr
        self.set_terminator("\n")
        self.request = None
        self.data = ''
        self.shutdown = 0
        self.scenario = None
        self.scenarioname = ''
        self.ui = ui
        self.require = 0
        self.try_reconnect = False
        asynchat.async_chat.__init__(self, sock)
        KalCache.init()

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
        except:
            traceback.print_exc()
            #self.failed(client, 'Invalid command <%s>' % cmd.lower())

    def handle_ok(self, args):
        self.ui.dispatch('on_ok', args)

    def handle_failed(self, args):
        self.ui.dispatch('on_failed', args)

    def handle_notify(self, args):
        self.ui.dispatch('on_notify', args)

    def handle_load(self, args):
        self.ui.dispatch('on_load', args)
        self.push('STATUS wait requirement\n')

    def handle_reset(self, args):
        self.ui.dispatch('on_reset')
        self.scenarioname = ''
        self.scenario = None

    def handle_game(self, args):
        self.scenario.update_server(args)

    def handle_require(self, args):
        scenarioname, filename, hash = args.split()
        if not KalCache.validate(scenarioname, filename, hash):
            self.push('GET %s %s\n' % (scenarioname, filename))
            self.require += 1

    def handle_write(self, args):
        scenarioname, filename, data = args.split()
        data = base64.urlsafe_b64decode(data)
        KalCache.write(scenarioname, filename, data)
        self.require -= 1
        if self.require == 0:
            self.handle_sync(scenarioname)

    def handle_sync(self, args):
        self.server.reconnect_count = 0
        if self.require != 0:
            self.push('STATUS still %s files to download\n' % self.require)
        else:
            self.push('STATUS loading\n')
            try:
                self.scenarioname = args
                pack = __import__('kaleidoscope.cache.%s' % self.scenarioname,
                                  fromlist=['client'])
                self.scenario = pack.client.scenario_class(self)
            except Exception, e:
                self.push('STATUS failed <%s>\n' % e)
                raise
            self.push('STATUS ready\n')

    def handle_error(self):
        if not self.try_reconnect:
            print 'KalClientChannel socket error'
            self.try_reconnect = True

    def handle_close(self):
        if not self.try_reconnect:
            print 'KalClientChannel socket closed'
            self.try_reconnect = True

    def log(self, message):
        print '<<<<<<<<<<<<<<<<<<<<<!!', message

class KalClient(asyncore.dispatcher):

    def __init__(self, host, port, ui):
        asyncore.dispatcher.__init__(self)
        self.addr = (host, port)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.channel = None
        self.ui = ui
        self.connect(self.addr)
        self.reconnect_count = 0
        Clock.schedule_interval(self.check_try_reconnect, 2.)

    def handle_connect(self):
        self.channel = KalClientChannel(self, self.socket, self.addr, self.ui)

    def check_try_reconnect(self, *largs):
        if not self.channel:
            return
        if self.channel.try_reconnect:
            print 'Retry to connect on the server (tentative %d)' % self.reconnect_count
            asyncore.dispatcher.__init__(self)
            self.reconnect_count += 1
            self.channel.close()
            self.channel = None
            self.ui.reset()
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect(self.addr)
            self.ui.dispatch('on_notify', 'Connexion sur %s (%d)' % (
                self.addr[0], self.reconnect_count))


class KalClientInteractive(Widget):
    def __init__(self, **kwargs):
        super(KalClientInteractive, self).__init__(**kwargs)
        self.nickname = kwargs.get('nickname', 'jubei')
        self.ip = kwargs.get('host', '127.0.0.1');
        self.port = kwargs.get('port', 6464)

        self.register_event_type('on_ok')
        self.register_event_type('on_failed')
        self.register_event_type('on_notify')
        self.register_event_type('on_load')
        self.register_event_type('on_reset')

        self.client = KalClient(self.ip, self.port, self)
        self.logged = False
        self.display_scenario = None
        self.history = []
        self.history_label = Label(text='-', font_size=42, size=Window.size)

        Clock.schedule_interval(self.update_loop, 0)
        Clock.schedule_interval(self.check_draw, 0)
        self.dispatch('on_notify', 'Connexion sur %s' % self.ip)

    def reset(self):
        self.logged = False
        for child in self.children[:]:
            self.remove_widget(child)

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

    def on_reset(self):
        self.children = []

    def on_notify(self, args):
        self.history.append(args)
        if len(self.history) > 4:
            self.history = self.history[1:]
        Logger.info('Kal: %s' % args)
        self.history_label.text = self.history[-1]

    def on_load(self, args):
        pass

    def check_draw(self, *largs):
        if self.display_scenario is None:
            self.add_widget(self.history_label)
            self.display_scenario = False

        if self.display_scenario is False:
            if self.client.channel and self.client.channel.scenario:
                self.display_scenario = True
                self.remove_widget(self.history_label)
                return

        if self.display_scenario is True:
            if not self.client.channel or not self.client.channel.scenario:
                self.display_scenario = False
                self.add_widget(self.history_label)
                return

    #
    # Obsolete part
    #
    '''

    def on_draw(self):
        super(KalClientInteractive, self).on_draw()
        self.draw_after()

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

    def draw_after(self):
        # if we have a scenario, draw it
        channel = self.client.channel
        if not channel:
            return
        if channel.scenario is None:
            return
        if not hasattr(channel.scenario, 'draw_after'):
            return
        channel.scenario.draw_after()
    '''

class KalClientInteractiveApp(App):
    def build(self):
        size = Window.size
        return KalClientInteractive(size=size, **self.options)
