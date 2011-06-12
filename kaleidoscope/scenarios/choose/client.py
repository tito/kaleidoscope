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

resource_add_path(dirname(__file__))

Builder.load_string('''
<PlaceButton>:
    size_hint: None, None
    font_size: 24
    halign: 'center'
    canvas.before:
        Color:
            rgba: (.5, .5, .5, .5) if not self.valid else [(.5, .5, .5, .5), (.5882, .7450, .1450, 1), (.9019, .2745, .121, 1), (.5058, .7921, .7843, 1), (.4980, .2235, .5450, 1)][self.idx]
        BorderImage:
            source: 'buttonbackground.png'
            pos: self.pos
            size: self.size
    canvas:
        Clear
        Color:
            rgba: self.color
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos: int(self.center_x - self.texture_size[0] / 2.), int(self.center_y - self.texture_size[1] / 2.)

<ChooseLabel>:
    font_size: 24
    anchor_x: 'center'
    anchor_y: 'middle'
    size_hint: None, None
    font_name: 'fonts/myriad.ttf'
''')

class PlaceButton(Button):
    valid = BooleanProperty(True)
    idx = NumericProperty(0)

class ChooseLabel(Label):
    pass

class ChooseClient(KalScenarioClient):
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
            ChooseLabel(text='Choisis une couleur',
                    pos=(0, cy + 200),
                    size=(Window.width, 100)
        ))
        for idx, px, py in ((1, cx-s-m, cy-s-m), (2, cx+m, cy-s-m),
                            (3, cx-s-m, cy+m), (4, cx+m, cy+m)):
            valid = idx in available
            button = PlaceButton(text='', size=(200, 200),
                              pos=(px, py), idx=idx, valid=valid)
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
            ChooseLabel(text='Choisis un scenario',
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
            ChooseLabel(text=u'Cliques lorsque tous les joueurs ont une place',
                    pos=(0, cy + 200),
                    size=(Window.width, 100)
        ))
        button = PlaceButton(text=u'Je suis pr\xeat',
                        size=(350, 100),
                        pos=(cx - 350 / 2., cy - 100))
        button.bind(on_release=beready_press)
        self.container.add_widget(button)

    def handle_wait(self, args):
        '''Wait someone
        '''
        cx, cy = Window.center
        self.container.clear_widgets()
        self.container.add_widget(
            ChooseLabel(text='Attends les autres joueurs',
                    pos=(0, cy + 200),
                    size=(Window.width, 100)
        ))
        self.container.add_widget(
            ChooseLabel(text=args,
                  pos=(0, cy - 50),
                  size=(Window.width, 100)
        ))

scenario_class = ChooseClient
