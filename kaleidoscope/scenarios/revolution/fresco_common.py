from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.graphics import Color, Rectangle, Line, BorderImage
from kivy.properties import StringProperty, ListProperty, \
        NumericProperty, ObjectProperty
from kivy.resources import resource_add_path
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.core.image import Image
from kivy.core.text import Label as CoreLabel
from json import load

from os.path import dirname, join

class FrescoDescription(FloatLayout):
    item = ObjectProperty(None)
    index = NumericProperty(-1)

class FrescoThumbnail(Scatter):
    fresco = ObjectProperty(None)
    item = ObjectProperty(None)
    popup = ObjectProperty(None)
    date = NumericProperty(None, allownone=True)
    index = NumericProperty(-1)

    def on_center(self, instance, value):
        self.date = self.fresco.get_date_from_pos(*value)

    def on_touch_down(self, touch):
        if not super(FrescoThumbnail, self).on_touch_down(touch):
            return
        if touch.is_double_tap:
            self.show_popup()
        return True

    def show_popup(self):
        if self.popup is not None:
            self.popup.dismiss()
        self.popup = popup = Popup(
            title=self.item['title'],
            content=FrescoDescription(item=self.item),
            size_hint=(.7, .7))
        popup.open()


class Fresco(Widget):

    json_filename = StringProperty('')
    data = ListProperty([])
    date_start = NumericProperty(0)
    date_end = NumericProperty(10)
    date_step = NumericProperty(1)

    def __init__(self, **kwargs):
        super(Fresco, self).__init__(**kwargs)
        self._trigger_build_canvas = Clock.create_trigger(
                self.build_canvas)
        self.bind(date_start=self._trigger_build_canvas,
                date_end=self._trigger_build_canvas,
                date_step=self._trigger_build_canvas,
                pos=self._trigger_build_canvas,
                size=self._trigger_build_canvas,
                size_hint=self._trigger_build_canvas,
                pos_hint=self._trigger_build_canvas)
        self.load()
        self._trigger_build_canvas()

    def load(self):
        curdir = join(dirname(__file__), 'data')
        json_filename = join(curdir, 'scenario.json')
        resource_add_path(curdir)
        with open(json_filename, 'r') as fd:
            data = load(fd)
        self.date_start = data['date_start']
        self.date_end = data['date_end']
        self.date_step = data['date_step']
        self.data = data['items']

    def set_pos_by_date(self, thumb, date):
        date -= self.date_start
        date /= float(self.date_end) - float(self.date_start)
        date *= self.width
        thumb.center = date - 64, self.center_y

    def get_thumb(self, index):
        item = self.data[index]
        return FrescoThumbnail(item=item, fresco=self, index=index)

    def get_date_from_pos(self, x, y):
        if not self.collide_point(x, y):
            return
        x -= self.x
        x /= float(self.width)
        x *= (self.date_end - self.date_start)
        x += self.date_start
        return x

    def build_canvas(self, dt):

        # get 3 textures
        curdir = dirname(__file__)
        arrow_left = Image(join(curdir, 'arrow_left.png')).texture
        arrow_middle = Image(join(curdir, 'arrow_middle.png')).texture
        arrow_right = Image(join(curdir, 'arrow_right.png')).texture

        self.canvas.before.clear()
        with self.canvas.before:
            cmax = ((self.date_end - self.date_start) / float(self.date_step))
            x, y = self.pos
            w, h = self.size
            fh = 100
            bh = 10
            cy = y + h / 2
            h = fh * 2
            r = range(self.date_start, self.date_end, self.date_step)
            for index, cx in enumerate(r):
                alpha = (cx - self.date_start) / (float(self.date_end) -
                        float(self.date_start))
                
                # create background of arrow (part of)
                c = 0.9 - (0.4 * alpha)
                a = 1.0 - 0.4 * alpha
                Color(c, c, c, a)

                if index == 0:
                    texture = arrow_left
                    border = (2, 2, 2, 8)
                elif index == len(r) - 1:
                    texture = arrow_right
                    border = (2, 126, 2, 2)
                else:
                    texture = arrow_middle
                    border = (2, 0, 2, 0)
                BorderImage(pos=(x, cy - fh), size=(w/cmax, h), texture=texture,
                        border=border)

                # create lines
                x = int(x)
                if index > 0:
                    Color(1, 1, 1, .8)
                    Line(points=[x, cy - fh - bh, x, cy + fh + bh])

                # create label (333f43)
                label = CoreLabel(text=str(cx),
                        font_size=14, font_name='fonts/DroidSans.ttf')
                label.refresh()
                Color(0x33/255., 0x3f/255., 0x43/255.)

                # trick to invert the label orientation
                tc = label.texture.tex_coords
                th, tw = label.texture.size
                tc = tc[-2:] + tc[0:-2]
                Rectangle(pos=(x + 5, cy - th / 2), size=(tw, th),
                        texture=label.texture, tex_coords=tc)
                x += w / cmax

class FrescoClientLayout(FloatLayout):
    fresco = ObjectProperty(None)

from kivy.factory import Factory
Factory.register('Fresco', cls=Fresco)
