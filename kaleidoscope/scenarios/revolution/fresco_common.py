# -*- coding: utf-8 -*-

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.graphics import Color, Rectangle, Line, BorderImage
from kivy.properties import StringProperty, ListProperty, \
        NumericProperty, ObjectProperty, BooleanProperty
from kivy.resources import resource_add_path
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.core.audio import SoundLoader
from json import load

from os.path import dirname, join

def update_size(instance, value):
    instance.text_size = (value[0], None)

class FrescoEmptyPlace(Widget):
    pass

class FrescoAudio(FloatLayout):
    source = StringProperty('')
    sound = ObjectProperty(None)

    def play_audio(self):
        source = self.source
        if not source:
            return
        if not self.sound:
            self.sound = SoundLoader.load(source)
        self.sound.play()

    def stop(self):
        if self.sound:
            self.sound.stop()

class FrescoDescription(FloatLayout):
    item = ObjectProperty(None)
    index = NumericProperty(-1)
    layout = ObjectProperty(None)
    media = ObjectProperty(None)

class FrescoThumbnail(Scatter):
    origin = ListProperty([0, 0])
    fresco = ObjectProperty(None)
    item = ObjectProperty(None)
    popup = ObjectProperty(None)
    date = NumericProperty(None, allownone=True)
    date_alpha = NumericProperty(None, allownone=True)
    have_date = BooleanProperty(False)
    index = NumericProperty(-1)
    length_flag = NumericProperty(0)
    color = ListProperty([92 / 255., 145 / 255., 179 / 255.])
    str_date = StringProperty('')
    auto_color = BooleanProperty(False)
    place_correctly = BooleanProperty(False)
    controled = BooleanProperty(False)
    real_center_y = NumericProperty(0)

    # used by server, to know which client have this item
    client = ObjectProperty(None)

    def on_date(self, instance, value):
        if value is None:
            self.str_date = ''
            self.date_alpha = None
            return
        months = (u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin',
                u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre',
                u'Décembre')
        self.date_alpha = self.fresco.get_alpha_from_realdate(value)
        y, m = self.fresco.get_dateinfo_from_alpha(self.date_alpha)
        self.str_date = u'%s %d' % (months[m-1], y)

        if self.auto_color:
            self.update_color()

    def update_color(self):
        if self.date is None:
            return
        now = self.date
        real = self.item['date']
        offset = self.fresco.date_allowed_offset
        diff = abs(now - real) / float(offset) * 2.

        color = Color(71 / 360., 71 / 100., 87 / 100., mode='hsv')
        if diff < 1.:
            color.h = 106 / 360.
            self.place_correctly = True
        else:
            h = (71 - 71 * (min(2., (diff - 1)) / 2.)) / 360.
            color.h = h
            self.place_correctly = False
        self.color = color.rgba

    def on_center(self, instance, value):
        if self.client is None and self.controled:
            self.date = self.fresco.get_date_from_pos(self.center_x, self.y + 60)
        have_date = self.date is not None
        if have_date != self.have_date:
            self.have_date = have_date

    def on_touch_down(self, touch):
        if not super(FrescoThumbnail, self).on_touch_down(touch):
            return
        Animation.stop_all(self, 'pos')
        self.controled = True
        if touch.is_double_tap:
            self.show_popup()
        return True

    def on_touch_up(self, touch):
        ret = super(FrescoThumbnail, self).on_touch_up(touch)
        if not self._touches:
            if not self.have_date:
                self.move_to_origin()
            if self.place_correctly:
                alpha_date = self.fresco.get_alpha_from_realdate(self.item['date'])
                self.fresco.set_pos_by_alpha(self, alpha_date, True)
                self.do_translation = False
        return ret

    def show_popup(self):
        if self.popup is not None:
            self.popup.dismiss()
        desc = FrescoDescription(item=self.item)

        count = 0
        content = self.item.get('content', '')
        if content:
            label = Label(text=content)
            label.bind(size=update_size)
            desc.layout.add_widget(label)
            count += 1
        media = self.item.get('media', '')
        if media:
            ext = media.rsplit('.', 1)[-1].lower()
            media = join(dirname(__file__), 'data', media)
            mediawidget = None
            if ext in ('mp3', 'wav', 'ogg'):
                mediawidget = FrescoAudio(source=media)
            elif ext in ('jpg', 'png', 'jpeg', 'gif', 'bmp', 'tga'):
                mediawidget = Image(source=media)
            else:
                pass
            if mediawidget:
                count += 1
                scatter = Scatter(do_translation=False, do_rotation=False,
                        min_scale=.4, max_scale=2)
                scatter.add_widget(mediawidget)
                scatter.bind(size=mediawidget.setter('size'))
                desc.layout.add_widget(mediawidget)
                desc.media = mediawidget

        desc.layout.cols = max(1, count)
        desc.layout.height = 500

        self.popup = popup = Popup(
            title=self.item['title'],
            content=desc,
            size_hint=(.7, .7))
        self.popup.bind(on_dismiss=self.stop_media)
        popup.open()

    def move_to_origin(self):
        Animation(pos=self.origin, t='out_elastic').start(self)

    def stop_media(self, instance):
        content = instance.content
        if not content.media:
            return
        try:
            content.media.stop()
        except Exception, e:
            print e


class Fresco(Widget):

    json_filename = StringProperty('')
    data = ListProperty([])
    date_start = NumericProperty(0)
    date_end = NumericProperty(10)
    date_step = NumericProperty(1)
    date_allowed_offset = NumericProperty(1)

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
        self.date_allowed_offset = data['date_allowed_offset']
        self.data = data['items']

    def set_pos_by_date(self, thumb, date, animate=False):
        thumb.size = (240, 140)
        thumb.controled = False
        thumb.date = date
        alpha = self.get_alpha_from_realdate(date)
        date = self.get_widgetdate_from_alpha(alpha)

        # convert widget date to widget position
        date -= self.date_start
        date /= float(self.date_end) - float(self.date_start)
        date *= self.width

        if animate:
            Animation(center_x=self.x + date, t='out_quad', d=.5).start(thumb)
        else:
            thumb.center_x = self.x + date
        if thumb.y == 0:
            thumb.center_y = self.center_y
            thumb.real_center_y = self.center_y
        self.update_thumbs_y()

    def set_pos_by_alpha(self, thumb, date_alpha, animate=False):
        thumb.size = (240, 140)
        date = self.get_widgetdate_from_alpha(date_alpha)

        # convert widget date to widget position
        date -= self.date_start
        date /= float(self.date_end) - float(self.date_start)
        date *= self.width

        thumb.center_x = self.x + date
        if animate:
            Animation(center_x=self.x + date, t='out_quad', d=.5).start(thumb)
        else:
            thumb.center_x = self.x + date
        if thumb.y == 0:
            thumb.center_y = self.center_y
            thumb.real_center_y = self.center_y
        self.update_thumbs_y()

    def update_thumbs_y(self):
        index = -1
        delta_table = {0:[], 1:[], 2:[], 3:[]}
        if isinstance(self.parent.parent, FrescoClientLayout):
            children = self.parent.parent.children
        else:
            children = self.parent.children
        for thumb in children:
            if not isinstance(thumb, FrescoThumbnail):
                continue
            index += 1

            # search a place in delta table
            found = None
            deltas = [9999, 9999, 9999, 9999]
            for index, items in delta_table.iteritems():
                for item in items:
                    delta = abs(thumb.center_x - item.center_x)
                    deltas[index] = min(deltas[index], delta)
                if deltas[index] > thumb.width:
                    # use that index, size we got a place
                    found = index
                    break
            if found is None:
                # no index found, use the smallest one
                delta = max(deltas)
                found = deltas.index(delta)
            i = found
            delta_table[i].append(thumb)
            if i == 0:
                delta = -120
            elif i == 1:
                delta = -260
            elif i == 2:
                delta = 120
            else:
                delta = 260
            center_y = self.center_y + delta
            if thumb.real_center_y == center_y:
                continue
            thumb.real_center_y = center_y
            Animation(center_y=center_y, t='out_elastic').start(thumb)


    def get_thumb(self, index):
        item = self.data[index]
        return FrescoThumbnail(item=item, fresco=self, index=index)

    def get_alpha_from_realdate(self, value):
        r = int(value * 10000)
        return r

    def get_dateinfo_from_alpha(self, value):
        # work on string
        value = str(value)
        return int(value[:-4]), int(value[-4:-2])

    def get_realdate_from_alpha(self, alpha):
        # return a real date (months goes from 1 to 12) from alpha
        years, months = self.get_dateinfo_from_alpha(alpha)
        return years + months / 100.

    def get_widgetdate_from_alpha(self, alpha):
        # return a widget date (months goes from 0 to 99)
        years, months = self.get_dateinfo_from_alpha(alpha)
        return years + (months - 1) / 0.12 / 100.

    def get_date_from_pos(self, x, y):
        if not self.collide_point(x, y):
            return
        x -= self.x
        x /= float(self.width)
        x *= (self.date_end - self.date_start)
        x += self.date_start 
        x *= 10000
        x = list(str(int(x)))
        x[-2:] = '00'
        x[-4:-2] = '%02d' % (int(float(''.join(x[-4:-2])) * 0.12) + 1)
        return self.get_realdate_from_alpha(int(''.join(x)))

    def set_date_by_alpha(self, thumb, alpha):
        thumb.date = self.get_realdate_from_alpha(alpha)

    def build_canvas(self, dt):

        # get 3 textures
        curdir = dirname(__file__)
        arrow_left = CoreImage(join(curdir, 'arrow_left.png')).texture
        arrow_middle = CoreImage(join(curdir, 'arrow_middle.png')).texture
        arrow_right = CoreImage(join(curdir, 'arrow_right.png')).texture

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
    inner_layout = ObjectProperty(None)
    logo = StringProperty('')
    color = ListProperty([1, 1, 1])
    time = NumericProperty(0)
    timelimit = NumericProperty(1)
    py = NumericProperty(None)

    def __init__(self, **kwargs):
        self.items = []
        self.emptyplaces = []
        super(FrescoClientLayout, self).__init__(**kwargs)

    def hide_places(self):
        for child in self.children[:]:
            if isinstance(child, FrescoEmptyPlace):
                self.remove_widget(child)
        Animation(size_hint_y=1., pos_hint={'y': 0},
                t='out_quad', d=.5).start(self.inner_layout)

    def create_emptyplace(self):
        return FrescoEmptyPlace()

    def create_and_add_item(self, index):
        thumb = self.fresco.get_thumb(index)
        thumb.color = self.color
        place = self.create_emptyplace()
        place.size = thumb.size
        self.add_widget(place)
        self.add_widget(thumb)
        self.items.append(thumb)
        self.emptyplaces.append(place)
        self.do_layout_all()
        return thumb

    def do_layout_all(self):
        self.do_layout_items(self.emptyplaces)
        self.do_layout_items(self.items)

    def do_layout_items(self, items):
        # place correctly thumbs
        if not items:
            return
        w, h = items[0].size
        margin = 20
        count_in_rows = int(self.width / (w + margin))
        rows_space = count_in_rows * w + (count_in_rows - 1 * margin)

        # starting point
        ox = x = (self.width - rows_space) / 2
        y = 20

        for item in items:
            item.pos = item.origin = x, y
            x += w + margin
            if x > self.width - margin * 2:
                x = ox
                y += h + margin
            

    def on_size(self, instance, value):
        self.do_layout_all()

    def on_pos(self, instance, value):
        self.do_layout_all()

    def on_inner_layout_y(self, instance, value):
        if self.py is None:
            self.py = value
            return
        diff = value - self.py
        self.py = value
        for thumb in self.children:
            if not isinstance(thumb, FrescoThumbnail):
                continue
            if thumb.have_date:
                thumb.center_y += diff / 2

    def on_inner_layout(self, instance, value):
        value.bind(y=self.on_inner_layout_y)

    def get_thumb_from_index(self, index):
        for thumb in self.children:
            if not isinstance(thumb, FrescoThumbnail):
                continue
            if thumb.index == index:
                return thumb
        return None


from kivy.factory import Factory
Factory.register('Fresco', cls=Fresco)
