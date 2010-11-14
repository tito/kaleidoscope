from os.path import join, dirname
from kaleidoscope.scenario import KalScenarioClient
from pymt import *
from OpenGL.GL import GL_REPEAT

background = Image(join(dirname(__file__), 'background.png'))
background.texture.wrap = GL_REPEAT
myriad_fontname = join(dirname(__file__), 'myriad.ttf')

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

class ChooseClient(KalScenarioClient):
    def draw(self):
        set_color(1)
        w, h = getWindow().size
        t = list(background.texture.tex_coords)
        t[2] = t[4] = w / float(background.width)
        t[5] = t[7] = h / float(background.height)
        drawTexturedRectangle(background.texture, size=getWindow().size,
                             tex_coords=t)

    def handle_place(self, args):
        '''Select a placement on the table
        '''
        def place_press(idx, *largs):
            self.send('PLACE %d' % idx)

        available = map(int, args.split())
        cx, cy = getWindow().center
        s = 200
        m = 10
        self.container.children = []
        self.container.add_widget(
            MTLabel(label='Choisi un emplacement',
                    cls='font', anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy + 200),
                    size=(getWindow().width, 100)
        ))
        for idx, px, py in ((1, cx-s-m, cy-s-m), (2, cx+m, cy-s-m),
                            (3, cx-s-m, cy+m), (4, cx+m, cy+m)):
            cls = 'valid' if idx in available else 'notvalid'
            button = MTButton(label='Place\n%s' % idx,
                              size=(200, 200), cls=['font', 'placebtn',
                                                    cls, 'idx%d' % idx],
                              pos=(px, py))
            self.container.add_widget(button)

            if cls == 'notvalid':
                continue

            button.connect('on_release', curry(place_press, idx))

    def handle_scenario(self, args):
        '''Select the scenario
        '''

        def scenario_press(scenario, *largs):
            self.send('SCENARIO %s' % scenario)

        cx, cy = getWindow().center
        s = 200
        m = 10
        self.container.children = []
        self.container.add_widget(
            MTLabel(label='Choisi un scenario',
                    cls='font', anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy + 200),
                    size=(getWindow().width, 100)
        ))

        py = cy
        for scenario, name in (
            ('pentaminos', 'Pentaminos'),
            ('anglais', 'Anglais')
        ):
            button = MTButton(label=name, size=(350, 100),
                              pos=(cx - 350 / 2., py - 100),
                              cls=['font', 'placebtn'])
            self.container.add_widget(button)
            py += 100 + m * 2

            button.connect('on_release', curry(scenario_press, scenario))

    def handle_beready(self, args):
        '''Be ready !
        '''

        def beready_press(scenario, *largs):
            self.send('READY')

        cx, cy = getWindow().center
        self.container.children = []
        self.container.add_widget(
            MTLabel(label=u'Cliquez une fois que tous les joueurs ont une place',
                    cls='font', anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy + 200),
                    size=(getWindow().width, 100)
        ))
        button = MTButton(label=u'Je suis pr\xeat',
                          cls=['font', 'placebtn'],
                          size=(350, 100),
                          pos=(cx - 350 / 2., cy - 50))
        button.connect('on_release', beready_press)
        self.container.add_widget(button)

    def handle_wait(self, args):
        '''Wait someone
        '''
        cx, cy = getWindow().center
        self.container.children = []
        self.container.add_widget(
            MTLabel(label='Attends les autres joueurs',
                    cls='font', anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy + 200),
                    size=(getWindow().width, 100)
        ))
        self.container.add_widget(
            MTLabel(label=args,
                    cls='font', anchor_x='center',
                    anchor_y='middle',
                    pos=(0, cy - 50),
                    size=(getWindow().width, 100)
        ))

scenario_class = ChooseClient
