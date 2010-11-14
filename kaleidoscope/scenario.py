import sys
import os
import hashlib

class KalScenarioServer(object):
    def __init__(self, game):
        super(KalScenarioServer, self).__init__()
        self.state = 'idle'
        self.running = False
        self.game = game
        self.clients = game
        self.controler = self.game.controler

    def sha224(self, resource):
        '''Do the md5 of a resource inside the scenario
        '''
        m = self.__module__
        module = sys.modules[m]
        directory = os.path.dirname(module.__file__)
        filename = os.path.join(directory, resource)
        with open(filename, 'rb') as fd:
            hash = hashlib.sha224(fd.read()).hexdigest()
        return hash

    def get(self, resource):
        '''Return data of a file
        '''
        if resource not in self.resources:
            return None
        m = self.__module__
        module = sys.modules[m]
        directory = os.path.dirname(module.__file__)
        filename = os.path.join(directory, resource)
        with open(filename, 'rb') as fd:
            data = fd.read()
        return data

    def update(self):
        '''Update the scenario (start if necessary)
        '''
        # ensure that the client list is ok
        self.clients = self.controler.clients

        # run/start
        if not self.running:
            self.start()
            self.running = True
        self.run()

    def send_to(self, client, message):
        self.controler.send_to(client, 'GAME %s\n' % message)

    def send_all(self, message):
        self.controler.send_all('GAME %s\n' % message)

    def msg_all(self, message):
        self.send_all('MSG %s' % message)

    def client_receive(self, client, args):
        c = args.split()
        if len(c) == 0:
            return
        cmd = c[0].lower()
        getattr(self, 'do_client_%s' % cmd)(client, c[1:])

    def run(self):
        '''Dispatch to the current state
        '''
        getattr(self, 'run_%s' % self.state)()

    def run_idle(self):
        '''Default state, nothing to do.
        '''
        pass

    def start(self):
        pass

    def stop(self):
        pass


class KalScenarioClient(object):
    def __init__(self, controler):
        super(KalScenarioClient, self).__init__()
        self.controler = controler
        self.ui = self.controler.ui
        self.container = self.ui

    def send(self, message):
        self.controler.push('GAME %s\n' % message)

    def update(self):
        pass

    def update_server(self, args):
        out = args.split(None, 1)
        if len(out) == 0:
            return
        if len(out) == 1:
            cmd = out[0]
            args = ''
        else:
            cmd, args = out
        try:
            getattr(self, 'handle_%s' % cmd.lower())(args)
        except Exception, e:
            print 'Unable to execute game command:', e
            import traceback
            traceback.print_exc()

    def start(self):
        pass

    def stop(self):
        pass

    def run(self):
        pass

