class KalScenarioServer(object):
    def __init__(self, game):
        super(KalScenarioServer, self).__init__()
        self.running = False
        self.game = game
        self.clients = game
        self.controler = self.game.controler

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

    def client_receive(self, client, args):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def run(self):
        pass


class KalScenarioClient(object):
    def __init__(self, controler):
        super(KalScenarioClient, self).__init__()
        self.controler = controler
        self.ui = self.controler.ui
        self.container = self.ui.container

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

