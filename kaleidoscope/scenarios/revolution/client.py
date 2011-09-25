from os.path import join, dirname
from time import time

from kaleidoscope.scenario import KalScenarioClient

from kivy.clock import Clock
from kivy.resources import resource_add_path
from kivy.lang import Builder

from fresco_common import FrescoClientLayout

resource_add_path(dirname(__file__))
Builder.load_file(join(dirname(__file__), 'fresco.kv'))

class FrescoClient(KalScenarioClient):
    def __init__(self, *largs):
        super(FrescoClient, self).__init__(*largs)
        self.count = 0
        self.timeout = 0
        self.layout = None
        self.logo = ''
        Clock.schedule_interval(self.update_graphics_timer, 1 / 10.)

    def handle_clear(self, args):
        pass

    def handle_waitready(self, args):
        pass

    def handle_time(self, args):
        self.timedelta, self.timeout = map(int, args.split())
        print 'time is', time(), self.timedelta
        self.timedelta = time() - self.timedelta
        print 'calculated timedelta', self.timedelta
        # apply that delta to timeout
        self.timeout += self.timedelta
        self.timelimit = self.timeout - time() 
        print 'time limit is', self.timelimit

    def handle_color(self, args):
        self.layout.color = map(lambda x: int(x) / 255., args.split())

    def handle_logo(self, args):
        self.layout.logo = args

    def handle_game1(self, args):
        self.layout = FrescoClientLayout()
        self.fresco = self.layout.fresco
        self.container.clear_widgets()
        self.container.add_widget(self.layout)

    def handle_give(self, args):
        # create thumbnail in the gridlayout
        self.count += 1
        index = int(args)
        item = self.layout.create_and_add_item(index)
        item.bind(date=self.send_date)

    def send_date(self, instance, value):
        if value is None:
            value = -1
        self.send('POS %d %d' % (instance.index, value))

    def update_graphics_timer(self, dt):
        if not self.layout:
            return
        t = self.timeout - time()
        if t < 0:
            t = 0
        self.layout.time = t
        self.layout.timelimit = self.timelimit



scenario_class = FrescoClient
