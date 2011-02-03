from os.path import dirname
from kaleidoscope.scenario import KalScenarioClient

from kivy.properties import NumericProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.resources import resource_add_path
from functools import partial

#background = Image(join(dirname(__file__), 'background.png'))
#myriad_fontname = join(dirname(__file__), 'myriad.ttf')

"""
css_add_sheet('''
.font {
    font-size: 24;
}

.placebtn {
    draw-alpha-background: 0;
    draw-background: 1;
    border-color: rgb(255, 255, 255, 126);
    border-width: 2;
    color: rgb(255, 255, 255);
    border-color-down: rgb(255, 255, 126);
    border-width-down: 4;
    draw-background-down: 1;
    bg-color-down: rgb(255, 255, 255, 50);
}

.idx1 { bg-color: #96be25; }
.idx2 { bg-color: #e6461f; }
.idx3 { bg-color: #81cac8; }
.idx4 { bg-color: #7f398b; }

.notvalid {
    draw-background: 0;
}
''')
"""

resource_add_path(dirname(__file__))

Builder.load_string('''
<PlaceButton>:
    font_size: 24
    halign: 'center'
    canvas.before:
        Color:
            rgba: (.5, .5, .5, .5) if not self.valid else [(.5, .5, .5, .5), (.5882, .7450, .1450, 1), (.9019, .2745, .121, 1), (.5058, .7921, .7843, 1), (.4980, .2235, .5450, 1)][self.idx]
        BorderImage:
            source: 'buttonbackground.png'
            pos: self.pos
            size: self.size
''')

class PlaceButton(Button):
    valid = BooleanProperty(True)
    idx = NumericProperty(0)

class ChooseClient(KalScenarioClient):
    def draw(self):
        set_color(1)
        w, h = Window.size
        t = list(background.texture.tex_coords)
        t[2] = t[4] = w / float(background.width)
        t[5] = t[7] = h / float(background.height)
        drawTexturedRectangle(background.texture, size=Window.size,
                             tex_coords=t)

    def handle_place(self, args):
        '''Select a placement on the table
        '''
        def place_press(idx, *largs):
            self.send('PLACE %d' % idx)

        available = map(int, args.split())
        cx, cy = Window.center
        s = 200
        m = 10
        self.container.clear_widgets()
        self.container.add_widget(
            Label(text='Choisis un emplacement',
                  font_size=24,
                  anchor_x='center',
                  anchor_y='middle',
                  pos=(0, cy + 200),
                  size=(Window.width, 100)
        ))
        for idx, px, py in ((1, cx-s-m, cy-s-m), (2, cx+m, cy-s-m),
                            (3, cx-s-m, cy+m), (4, cx+m, cy+m)):
            valid = idx in available
            button = PlaceButton(text='Place\n%s' % idx, idx=idx,
                              size=(200, 200), valid=valid,
                              pos=(px, py))
            self.container.add_widget(button)

            if not valid:
                continue

            button.bind(on_release=partial(place_press, idx))

    def handle_scenario(self, args):
        '''Select the scenario
        '''

        def scenario_press(scenario, *largs):
            self.send('SCENARIO %s' % scenario)

        cx, cy = Window.center
        s = 200
        m = 10
        self.container.clear_widgets()
        self.container.add_widget(
            Label(text='Choisis un scenario',
                    font_size=24, anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy + 200),
                    size=(Window.width, 100)
        ))

        py = cy
        for scenario, name in (
            ('pentaminos', 'Pentaminos'),
            #('anglais', 'Anglais')
        ):
            button = PlaceButton(text=name, size=(350, 100),
                            pos=(cx - 350 / 2., py - 100))
            self.container.add_widget(button)
            py += 100 + m * 2

            button.bind(on_release=partial(scenario_press, scenario))

    def handle_beready(self, args):
        '''Be ready !
        '''

        def beready_press(*largs):
            self.send('READY')

        cx, cy = Window.center
        self.container.clear_widgets()
        self.container.add_widget(
            Label(text=u'Cliques lorsque tous les joueurs ont une place',
                    font_size=24, anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy + 200),
                    size=(Window.width, 100)
        ))
        button = PlaceButton(text=u'Je suis pr\xeat',
                        size=(350, 100),
                        pos=(cx - 350 / 2., cy - 50))
        button.bind(on_release=beready_press)
        self.container.add_widget(button)

    def handle_wait(self, args):
        '''Wait someone
        '''
        cx, cy = Window.center
        self.container.clear_widgets()
        self.container.add_widget(
            Label(text='Attends les autres joueurs',
                    font_size=24, anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy + 200),
                    size=(Window.width, 100)
        ))
        self.container.add_widget(
            Label(text=args,
                  font_size=24, anchor_x='center',
                  anchor_y='middle',
                  pos=(0, cy - 50),
                  size=(Window.width, 100)
        ))

scenario_class = ChooseClient
