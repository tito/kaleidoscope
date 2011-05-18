__all__ = ('PentaContainer', 'PentaListContainer')

from penta_color import *
from kivy.utils import get_color_from_hex
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.core.window import Window

class PentaContainer(Widget):

    string = StringProperty(None)

    def __init__(self, **kwargs):
        super(PentaContainer, self).__init__(**kwargs)
        self.pw = 0
        self.ph = 0
        self.pentak = ''
        self.color = None
        self.server = kwargs.get('server', False)

    def on_string(self, instance, value):
        self.canvas.clear()
        if value is None:
            return
        with self.canvas:
            Color(1, 1, 1, .5)
            Rectangle(pos=self.pos, size=self.size)

            if self.color is None:
                self.color = get_color_from_hex(penta_colors[self.pentak])

            step = self.width / 7
            ox, oy = self.pos

            Color(*self.color)
            size = (step, step)
            pw = self.pw
            ph = self.ph
            s = self.string
            ox += step + (step * (5 - pw)) / 2.
            oy += step + (step * (5 - ph)) / 2.
            for ix in xrange(pw):
                for iy in xrange(ph):
                    if s[iy * pw + ix] != '1':
                        continue
                    x = ix * (step + 1)
                    y = iy * (step + 1)
                    Rectangle(pos=(ox + x, oy + y), size=size)

class PentaListContainer(BoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault('spacing', 10)
        kwargs.setdefault('server', False)
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('invert', True)
        kwargs.setdefault('size_hint', (None, None))
        w = Window.width
        x = y = 0
        h = 90
        if kwargs['server']:
            x = 10
            y = Window.height / 2. - 45
            h = 74.5
        kwargs.setdefault('size', (w, h))
        kwargs.setdefault('pos', (x, y))
        super(PentaListContainer, self).__init__(**kwargs)
        count = 6
        if kwargs['server']:
            count = 12
        for x in xrange(count):
            self.add_widget(PentaContainer(size=(h, h),
                                          server=kwargs['server']))
        self.idx = 0

    def add_penta(self, k, penta, w, h):
        # check that penta don't exist yet in our children
        for child in self.children:
            if child.pentak == k:
                return False
        self.children[self.idx].pentak = k
        self.children[self.idx].string = penta
        self.children[self.idx].pw = w
        self.children[self.idx].ph = h
        self.idx += 1
        return True

    def remove_last(self):
        self.idx -= 1
        self.children[self.idx].string = None
