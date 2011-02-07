__all__ = ('PentaContainer', 'PentaListContainer')

from OpenGL.GL import GL_LINE_LOOP
from pymt import *
from penta_color import *
from pymt.parser import parse_color

class PentaContainer(MTWidget):
    def __init__(self, **kwargs):
        super(PentaContainer, self).__init__(**kwargs)
        self.string = None
        self.pw = 0
        self.ph = 0
        self.pentak = ''
        self.color = None
        self.server = kwargs.get('server', False)

    def draw(self):
        if self.server:
            set_color(1, 1, 1, .5)
            drawRectangle(pos=self.pos, size=self.size, style=GL_LINE_LOOP)

        if not self.string:
            return

        if self.color is None:
            self.color = parse_color(penta_colors[self.pentak])

        step = self.width / 7
        ox, oy = self.pos

        set_color(*self.color)
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
                drawRectangle(pos=(ox + x, oy + y), size=size)

class PentaListContainer(MTBoxLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault('spacing', 10)
        kwargs.setdefault('server', False)
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('invert', True)
        kwargs.setdefault('size_hint', (None, None))
        w = getWindow().width
        h = 90
        kwargs.setdefault('size', (w, h))
        y = 0
        x = y = 0
        if kwargs['server']:
            x = 40
            y = getWindow().height / 2. - 45
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
            if child.string == penta:
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
