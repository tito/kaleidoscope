from random import random, randint
from os.path import join, dirname
from time import time

from kaleidoscope.scenario import KalScenarioClient

from kivy.core.window import Window
from kivy.core.image import Image
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.utils import get_color_from_hex
from kivy.vector import Vector
from kivy.animation import Animation
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty, NumericProperty
from kivy.resources import resource_add_path
from kivy.lang import Builder
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock

from fresco_common import FrescoClientLayout

resource_add_path(dirname(__file__))
Builder.load_file(join(dirname(__file__), 'fresco.kv'))

background = Image(join(dirname(__file__), 'background.png'))
background.texture.wrap = 'repeat'

class FrescoClient(KalScenarioClient):
    def __init__(self, *largs):
        super(FrescoClient, self).__init__(*largs)
        self.count = 0
        self.timeout = 0
        self.timeoutl = .1
        self.layout = None

    def handle_clear(self, args):
        pass

    def handle_waitready(self, args):
        pass

    def handle_time(self, args):
        self.timeout = int(args)
        self.timeoutl = self.timeout - time()

    def handle_game1(self, args):
        self.layout = FrescoClientLayout()
        self.fresco = self.layout.fresco
        self.container.clear_widgets()
        self.container.add_widget(self.layout)

    def handle_give(self, args):
        # create thumbnail in the gridlayout
        self.count += 1
        index = int(args)
        item = self.fresco.get_thumb(index)
        item.bind(date=self.send_date)
        item.pos = (100 + self.count * 150, 100)
        self.layout.add_widget(item)

    def send_date(self, instance, value):
        if value is None:
            value = -1
        self.send('POS %d %d' % (instance.index, value))



scenario_class = FrescoClient
