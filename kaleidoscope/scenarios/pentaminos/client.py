from os.path import join, dirname
from kaleidoscope.scenario import KalScenarioClient
from pymt import *
from pymt.parser import parse_color
from random import random, randint
from OpenGL.GL import *
from penta_color import *

# local
from penta_color import *

css_add_sheet('''
pentaminoassembled,
pentaminosquare {
    draw-background: 1;
    bg-color: rgb(255, 255, 255);
}

pentalistcontainer {
    draw-background: 0;
}

.pentabtn {
    draw-alpha-background: 0;
    draw-background: 0;
    border-color: rgb(255, 255, 255);
    border-width: 2;
    font-size: 24;
    color: rgb(255, 255, 255);
    border-color-down: rgb(255, 255, 255);
    border-width-down: 4;
    draw-background-down: 1;
    bg-color-down: rgb(255, 255, 255, 50);
}
''')

square_background = Image(join(dirname(__file__), 'penta-square.png'))
square_shadow = Image(join(dirname(__file__), 'penta-square-shadow.png'))
penta_background = Image(join(dirname(__file__), 'penta-background.png'))
penta_background.texture.wrap = GL_REPEAT
penta_background_bottom = Image(join(dirname(__file__), 'penta-background-bottom.png'))
background = Image(join(dirname(__file__), 'background.png'))
background.texture.wrap = GL_REPEAT
myriad_fontname = join(dirname(__file__), 'myriad.ttf')

SQUARE = 100
SQUARE_MM = 75
SQUARE_M = 5

class PentaContainer(MTWidget):
    def __init__(self, **kwargs):
        super(PentaContainer, self).__init__(**kwargs)
        self.string = None
        self.pw = 0
        self.ph = 0
        self.pentak = ''
        self.color = None

    def draw(self):
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
        kwargs.setdefault('orientation', 'horizontal')
        kwargs.setdefault('invert', True)
        kwargs.setdefault('size_hint', (1, None))
        w, h = getWindow().size
        h = 100
        kwargs.setdefault('height', h)
        kwargs.setdefault('pos', (0, 0))
        super(PentaListContainer, self).__init__(**kwargs)
        for x in xrange(6):
            self.add_widget(PentaContainer(size=(h, h)))
        self.idx = 0

    def add_penta(self, k, penta, w, h):
        self.children[self.idx].pentak = k
        self.children[self.idx].string = penta
        self.children[self.idx].pw = w
        self.children[self.idx].ph = h
        self.idx += 1

class PentaminoAssembled(MTScatter):
    def __init__(self, key, pw, ph, string, **kwargs):
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('size', map(lambda x: int(x) * (SQUARE + SQUARE_M) - SQUARE_M, (pw, ph)))
        super(PentaminoAssembled, self).__init__(**kwargs)

        self.string = string
        self.pw = int(pw)
        self.ph = int(ph)
        self.key = key
        self.color = parse_color(penta_colors[key])
        self.highlight = None

    def turn_left(self, coords, orientation):
        if orientation == 0:
            return coords

        # turn all
        out = []
        minx, miny = 999, 999
        for x, y in coords:
            nx = x
            ny = y
            for i in xrange(orientation):
                nx, ny = -ny, nx
            if nx < minx:
                minx = nx
            if ny < miny:
                miny = ny
            out.append((nx, ny))

        # now, ensure it's 0, 0
        out2 = []
        for x, y in out:
            out2.append((x - minx, y - miny))

        return out2

    def check_from(self, x, y, rotation):
        # get drop point (+ trick for drop zone)
        px, py = self.pos
        dx, dy = self.parent.position_in_grid(px, py)

        # convert to our ix, iy
        x, y = self.to_local(x, y)
        x = int(x / (SQUARE + SQUARE_M))
        y = int(y / (SQUARE + SQUARE_M))
        orientation = int(((rotation + 1) % 360) / 90)

        coords_to_test = []
        pw = self.pw
        ph = self.ph
        s = self.string
        for ix in xrange(pw):
            for iy in xrange(ph):
                if s[iy * pw + ix] != '1':
                    continue
                coords_to_test.append((ix, iy))

        coords_to_test = self.turn_left(coords_to_test, orientation)

        # rotate x/y too
        for i in xrange(orientation):
            x, y = -y, x

        result = []
        for cx, cy in coords_to_test:
            result.append((cx + dx, cy + dy))
        self.highlight = result
        return result

    def on_touch_down(self, touch):
        '''Remove the square in the grid if exist
        '''
        if super(PentaminoAssembled, self).on_touch_down(touch):
            self.parent.remove_square(self)
            return True
        return False

    def on_touch_move(self, touch):
        '''Select only our touch, and detect position on the grid
        '''
        if not super(PentaminoAssembled, self).on_touch_move(touch):
            return
        if not touch.grab_state:
            return
        self.check_from(touch.x, touch.y, self.rotation)
        return True

    def on_touch_up(self, touch):
        if not super(PentaminoAssembled, self).on_touch_up(touch):
            return
        if not touch.grab_state:
            return
        rot = self.rotation - self.rotation % 90
        self.do(Animation(rotation=rot,
                          d=.1, f='ease_out_cubic'))
        # ensure that all coords fit in the grid
        fit = True
        coords = self.check_from(touch.x, touch.y, rot)
        gw, gh = self.parent.client.gridsize
        p = self.parent
        for ix, iy in coords:
            if ix < 0 or iy < 0 or ix >= gw or iy >= gh:
                fit = False
                break
            if p.grid[ix][iy]:
                fit = False
                break
        if fit:
            for x, y in coords:
                p.drop_square(self, x, y)
            # align to the grid
            ix, iy = p.position_in_grid(*self.pos)
            self.do(Animation(
                pos=(p.mx + ix * p.step, p.my + iy * p.step),
                f='ease_out_cubic', d=.1))
        self.highlight = None
        return True

    def draw(self):
        set_color(*self.color)
        size = (SQUARE, SQUARE)
        pw = self.pw
        ph = self.ph
        s = self.string
        for ix in xrange(pw):
            for iy in xrange(ph):
                if s[iy * pw + ix] != '1':
                    continue
                x = ix * (SQUARE + SQUARE_M)
                y = iy * (SQUARE + SQUARE_M)
                drawRectangle(pos=(x, y), size=size)

class PentaminoSquare(MTScatter):
    def __init__(self, **kwargs):
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_rotate', False)
        kwargs.setdefault('size', (SQUARE, SQUARE))
        super(PentaminoSquare, self).__init__(**kwargs)
        self.highlight = None
        self.drawmode = 'normal'

    def on_touch_down(self, touch):
        '''Remove the square in the grid if exist
        '''
        if super(PentaminoSquare, self).on_touch_down(touch):
            self.parent.remove_square(self)
            return True
        return False

    def on_touch_move(self, touch):
        '''Select only our touch, and detect position on the grid
        '''
        if not super(PentaminoSquare, self).on_touch_move(touch):
            return
        if not touch.grab_state:
            return
        cx, cy = self.center
        ix, iy = self.parent.collide_grid(cx, cy)
        if ix == -1:
            self.highlight = None
            return
        self.highlight = [(ix, iy)]

    def on_touch_up(self, touch):
        '''Drop the square on the grid if it's possible
        '''
        if not super(PentaminoSquare, self).on_touch_up(touch):
            return
        if not touch.grab_state:
            return
        cx, cy = self.center
        ix, iy = self.parent.collide_grid(cx, cy)
        if ix == -1:
            return
        self.parent.drop_square(self, ix, iy)
        self.highlight = None

    def draw(self):
        set_color(1, blend=True)
        if self.drawmode == 'shadow':
            drawTexturedRectangle(texture=square_shadow.texture, size=(SQUARE,SQUARE))
        else:
            drawTexturedRectangle(texture=square_background.texture, size=(SQUARE,SQUARE))

class PentaminosContainer(MTWidget):
    def __init__(self, client, **kwargs):
        super(PentaminosContainer, self).__init__(**kwargs)
        self.client = client
        gw, gh = self.client.gridsize
        self.reset()
        self.last_msg = ''
        self.done = []
        self.backy = 0
        self.do(Animation(backy=self.height - 100, f='ease_out_elastic'))

    def reset(self):
        self.children.clear()
        self.grid = []
        gw, gh = self.client.gridsize
        for x in xrange(gw):
            self.grid.append([])
            for y in xrange(gh):
                self.grid[-1].append(None)

    def position_in_grid(self, x, y):
        '''Get the x/y index in the grid for a x/y position on screen
        (not bounded)
        '''
        gw, gh = self.client.gridsize
        step = self.step
        mx = self.mx
        my = self.my

        ix = ((x - mx) / step)
        iy = ((y - my) / step)
        return map(int, (ix, iy))

    def collide_grid(self, x, y):
        '''Get the X/Y index in the grid for an x/y position on screen
        '''
        gw, gh = self.client.gridsize
        ix, iy = self.position_in_grid(x, y)
        if ix < 0 or iy < 0 or ix >= gw or iy >= gh:
            return -1, -1
        return ix, iy

    @property
    def my(self):
        '''Return the Y margin to start drawing
        '''
        return self.height - self.backy + 100

    @property
    def mx(self):
        '''Return the X margin to start drawing
        '''
        w, h = self.size
        gw, gh = self.client.gridsize
        return (w - gw * (SQUARE + SQUARE_M)) / 2.

    @property
    def step(self):
        '''Return the step between each square
        '''
        return SQUARE + SQUARE_M

    def drop_square(self, square, ix, iy):
        '''A square is dropped somewhere
        '''
        grid = self.grid
        if grid[ix][iy] is not None:
            return
        grid[ix][iy] = square
        if isinstance(square, PentaminoSquare):
            square.do(Animation(
                pos=(self.mx + ix * self.step, self.my + iy * self.step),
                f='ease_out_cubic', d=.1))

    def remove_square(self, square):
        '''Remove a square from the grid
        '''
        gw, gh = self.client.gridsize
        g = self.grid
        for x in xrange(gw):
            for y in xrange(gh):
                if g[x][y] == square:
                    g[x][y] = None

    def nearest_square(self, current):
        cpos = Vector(current.pos)
        nearest_d = 999
        nearest_child = None
        for child in self.children:
            if not isinstance(child, PentaminoSquare):
                continue
            if child is current:
                continue
            d = cpos.distance(child.pos)
            if d < nearest_d:
                nearest_d = d
                nearest_child = child
        return nearest_child, nearest_d


    def on_update(self):
        super(PentaminosContainer, self).on_update()
        if self.client.gametype == 'game1':
            self.check_grid_pentamino()

    def check_grid_pentamino(self):
        k = self.is_pentamino()
        if not k:
            return
        if k in self.done:
            # TODO do an error
            return
        # add to our list
        penta, w, h = self.client.pcontainer.get_pentamino()
        self.client.lcontainer.add_penta(k, penta, w, h)
        self.done.append(k)
        # send to server
        self.client.send('PENTAMINO %s %d %d %s' % (k, w, h, penta))
        self.client.pcontainer.reset()

    def is_pentamino(self):
        penta, w, h = self.get_pentamino()
        if w == 0 or h == 0:
            return
        return self.search_pentamino(penta, w, h)

    def search_pentamino(self, penta, w, h):
        penta_size = (w, h)
        for k, possibilities in penta_schemes.iteritems():
            for d_size, d_penta in possibilities:
                if penta_size != d_size:
                    continue
                if penta != d_penta:
                    continue
                return k
        return None

    def get_pentamino(self):
        '''After most calculation done, the best and fast way is to test every pentaminos.
        1. linearize the grid
        2. check if we can simplify, if yes, go back to 1.
        3. check on our dataset
        '''

        gw, gh = self.client.gridsize
        grid = self.grid

        do_simplify = True
        rm_x = []
        rm_y = []

        # linearize the grid / simplify
        while do_simplify:
            do_simplify = False

            penta = ''
            simplified_penta = ''
            # need 5 square in the grid.
            for y in xrange(gh):
                for x in xrange(gw):
                    e = grid[x][y]
                    if e:
                        penta += '1'
                    else:
                        penta += '.'
                    if x in rm_x or y in rm_y:
                        continue
                    if e:
                        simplified_penta += '1'
                    else:
                        simplified_penta += '.'

            # simplify cols (left)
            for x in xrange(gw):
                if '1' in penta[x::gw]:
                    break
                if x not in rm_x:
                    rm_x.append(x)
                    do_simplify = True

            # simplify cols (right)
            for x in xrange(gw-1, 0, -1):
                if '1' in penta[x::gw]:
                    break
                if x not in rm_x:
                    rm_x.append(x)
                    do_simplify = True

            # simplify lines (bottom)
            for y in xrange(gh):
                idx = y * gw
                if '1' in penta[idx:idx+gw]:
                    break
                if y not in rm_y:
                    rm_y.append(y)
                    do_simplify = True

            # simplify lines (top)
            for y in xrange(gh-1, 0, -1):
                idx = y * gw
                if '1' in penta[idx:idx+gw]:
                    break
                if y not in rm_y:
                    rm_y.append(y)
                    do_simplify = True

        return (simplified_penta, gw - len(rm_x), gh - len(rm_y))

    def on_draw(self):
        '''Hack to be able to draw children ok + highlight + children moving
        '''
        self.draw()
        self.draw_after()
        for x in self.children:
            x.drawmode = 'shadow'
            x.dispatch_event('on_draw')
            x.drawmode = ''
        for x in self.children:
            x.dispatch_event('on_draw')

    def draw(self):
        w, h = getWindow().size
        set_color(1)
        b = self.backy - penta_background_bottom.height
        t = list(penta_background.texture.tex_coords)
        t[2] = t[4] = w / float(penta_background.width)
        t[5] = t[7] = b / float(penta_background.height)
        drawTexturedRectangle(texture=penta_background.texture,
                              pos=(0, h - b),
                              size=(w, b),
                              tex_coords=t)
        set_color(1, blend=True)
        drawTexturedRectangle(texture=penta_background_bottom.texture,
                              pos=(0, h - self.backy),
                              size=(w, penta_background_bottom.height))

        gw, gh = self.client.gridsize
        step = self.step
        mx = self.mx
        my = self.my
        s = (SQUARE, SQUARE)
        y = self.my
        set_color(1, 1, 1, .5)
        for iy in xrange(gh):
            x = mx
            for ix in xrange(gw):
                drawRectangle(pos=(x, y), size=s, style=GL_LINE_LOOP)
                x += SQUARE + SQUARE_M
            y += SQUARE_M + SQUARE

    def draw_after(self):
        '''Draw highlights
        '''
        gw, gh = self.client.gridsize
        s = (SQUARE, SQUARE)
        grid = self.grid
        step = self.step
        mx = self.mx
        my = self.my
        for x in self.children:
            if not x.highlight:
                continue
            for ix, iy in x.highlight:
                if ix < 0 or ix >= gw or iy < 0 or iy >= gh:
                    continue
                if grid[ix][iy] is None:
                    set_color(.9, .9, .9, .7)
                else:
                    set_color(1, .2, .2, .7)
                drawRectangle(pos=(mx + ix * step, my + iy * step), size=s)


class PentaminosClient(KalScenarioClient):
    def __init__(self, *largs):
        super(PentaminosClient, self).__init__(*largs)
        self.color = (.2, .2, .2, 0)
        self.current_color = (.2, .2, .2, 0)
        self.text_color = (1, 1, 1, 1)
        self.current_text_color = (1, 1, 1, 1)
        self.count = 0
        self.gridsize = 0, 0
        self.last_msg = ''
        self.gametype = 'none'

    def handle_clear(self, args):
        self.pcontainer.reset()

    def handle_penta(self, args):
        c = args.split()
        key, w, h, string = c
        r = randint(0, 3) * 90
        y = self.pcontainer.height - 200
        x = 100 + random() * (self.pcontainer.width - 200)
        p = PentaminoAssembled(key, w, h, string,
                          center=(x, y), rotation=r, scale=.0001)
        p.do(Delay(d=random() * 1) + Animation(scale=1, f='ease_out_elastic', d=1))
        self.pcontainer.add_widget(p)

    def handle_size(self, args):
        self.gridsize = map(int, args.split())
        if hasattr(self, 'pcontainer'):
            self.pcontainer.reset()

    def handle_msg(self, message):
        self.last_msg = message

    def handle_waitready(self, message):
        self.container.children = []
        btn = MTLabel(label='En attente...', cls=['pentabtn', 'ready'],
                size=(200, 100))
        anchor = MTAnchorLayout(size=self.container.size)
        anchor.add_widget(btn)
        self.container.add_widget(anchor)

    def handle_game1(self, args):
        self.container.children = []
        self.gametype = 'game1'
        self.pcontainer = PentaminosContainer(self, size=getWindow().size)
        self.lcontainer = PentaListContainer()
        self.container.add_widget(self.lcontainer)
        self.container.add_widget(self.pcontainer)

    def handle_game2(self, args):
        self.container.children = []
        self.gametype = 'game2'
        self.container.remove_widget(self.lcontainer)

    def handle_give(self, args):
        l = int(args)
        self.count = l
        w, h = getWindow().size

        x = (w - (SQUARE + SQUARE_MM) * (l-1)) / 2.
        y = h - SQUARE_MM
        for n in xrange(self.count):
            p = PentaminoSquare(center=(x, y), scale=.0001)
            p.do(Delay(d=random() * 1) + Animation(scale=1, center=(x, y), f='ease_out_elastic', d=1))
            x += SQUARE + SQUARE_MM
            self.pcontainer.add_widget(p)

    def handle_color(self, args):
        bg, fg = map(parse_color, args.split())
        self.color = bg
        self.text_color = fg

    def draw(self):
        set_color(1)
        w, h = getWindow().size
        t = list(background.texture.tex_coords)
        t[2] = t[4] = w / float(background.width)
        t[5] = t[7] = h / float(background.height)
        drawTexturedRectangle(background.texture, size=getWindow().size,
                             tex_coords=t)

    def draw_after(self):
        msg = self.last_msg
        if not msg:
            return
        if self.gametype == 'game1':
            y = self.pcontainer.height - self.pcontainer.backy + 30
        else:
            y = 130

        w, h = getWindow().size
        set_color(1)
        drawLabel(label=msg, pos=(w / 2., y), center=False,
                  anchor_x='center',
                  font_name=myriad_fontname,
                  color=self.current_text_color,
                  font_size=24)


scenario_class = PentaminosClient
