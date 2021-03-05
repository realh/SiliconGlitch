import random
import operator
from functools import reduce
from cairo import Context, Format, ImageSurface
import render
from mipmaps import MipMapGenerator

NUM_STRIPS = 16
# I think in TM1/Forever the specular RGB determine what colour it shines,
# alpha is shininess. In TM2 the R and G are used for something else and B is
# zero.
BACKGROUND_SPECULAR1 = 0.25
BACKGROUND_SPECULAR2 = 0.333
BACKGROUND_BUMPINESS = 0.2
FOREGROUND_SPECULAR = 0.5

class GlitchRectBackground:
    """ Main 2:1 rectangle texture """
    def __init__(self, width, height, strip1, strip2, z1, z2):
        """ width: Width in pixels
            height: Height in pixels
            strip1: Diffuse colour of odd strips (r, g, b (, a)): float
            strip2: Diffuse colour of even strips
            z1: Height of odd strips in bump map
            z2: Height of even strips in bump map """
        self.width = width
        self.height = height
        self.strip1 = strip1
        self.strip2 = strip2
        self.z1 = z1
        self.z2 = z2

    def get_renderables(self):
        strips = []
        sw = self.width / NUM_STRIPS
        for n in range(NUM_STRIPS):
            if n % 2:
                d = self.strip1
                b = 0
                s = self.strip1[:3] + (BACKGROUND_SPECULAR1,)
            else:
                d = self.strip2
                b = BACKGROUND_BUMPINESS
                s = self.strip2[:3] + (BACKGROUND_SPECULAR2,)
            strips.append(render.Rect(d, s, b, n * sw, 0, sw, self.height))
        return strips

class Rect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


# Squarish blocks are added with dimension limits according to these constants.
RAND_SQ_BASE = 8
RAND_SQ_MIN = 3
RAND_SQ_MAX = 5
RAND_SQ_PADDING = RAND_SQ_BASE


def fill_random_squarishes(rects, width, height):
    """ rects is a list of lists. Each inner list contains 1, 2 or 4 Rects, so
    that rects near edges or corners are duplicated for tilability in an
    eclosing rect of width x height. The outer list may be empty at input. This
    function adds rects until the enclosing space is "fullish". """
    new_rects = []
    attempts = 0
    RSP = RAND_SQ_PADDING
    while attempts < 10:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        w = random.randint(RAND_SQ_MIN, RAND_SQ_MAX)
        h = 0
        while w - h > 1 or h - w > 1:
            h = random.randint(RAND_SQ_MIN, RAND_SQ_MAX)
        w *= RAND_SQ_BASE
        h *= RAND_SQ_BASE
        clash = False
        group = [Rect(x, y, w, h)]
        if x + w > width:
            group.append(Rect(x - width, y, w, h))
        if y + h > height:
            group.append(Rect(x, y - height, w, h))
            if x + w > width:
                group.append(Rect(x - width, y - height, w, h))
        for og in rects:
            for oldr in og:
                for newr in group:
                    if newr.x <= oldr.x + oldr.w + RSP and \
                            newr.x + newr.w + RSP >= oldr.x and \
                            newr.y <= oldr.y + oldr.h + RSP and \
                            newr.y + newr.h + RSP >= oldr.y:
                        attempts += 1
                        clash = True
                        break
                if clash:
                    break
            if clash:
                break
        if not clash:
            attempts = 0
            rects.append(group)


STRIP1 = (0.2, 0.275, 0.4)
STRIP2 = (0.25, 0.35, 0.5)


class GlitchRectMipMaps(MipMapGenerator):
    def __init__(self, width, height, strip1, strip2, basename):
        """ Parameters are the same as for GlitchRectBackground. """
        super().__init__(width, height, basename)
        self.strip1 = strip1
        self.strip2 = strip2
        self.make_squarishes()

    def make_squarishes(self):
        squarishes = []
        fill_random_squarishes(squarishes, self.width, self.height)
        self.add_texture_to_squarishes(squarishes)
        self.squarishes = squarishes

    def add_texture_to_squarishes(self, squarishes, from_index = 0):
        j = from_index
        while j < len(squarishes):
            group = squarishes[j]
            grey = 0.7 + random.random() * 0.1
            spec = (grey, grey, grey, FOREGROUND_SPECULAR)
            # TODO: Randomise spec a bit
            grey = (grey, grey, grey, 0.9)
            for i in range(len(group)):
                r = group[i]
                group[i] = render.Rect(grey, spec, 1, r.x, r.y, r.w, r.h)
            j += 1

    def prepare_layer(self, layer, w, h):
        if layer == 0:
            return
        # Remove about a quarter of the squarishes
        squarishes = self.squarishes[:len(self.squarishes) * 3 // 4]
        # TODO: Change the specular of remaining squarishes
        l = len(squarishes)
        # Refill
        fill_random_squarishes(squarishes, self.width, self.height)
        self.add_texture_to_squarishes(squarishes, l)
        self.squarishes = squarishes
        
    def render_layer(self, layer, method, w, h):
        alpha = len(self.strip1) == 4 or method != "diffuse"
        if alpha:
            fmt = Format.ARGB32
        else:
            fmt = Format.RGB24
        img = ImageSurface(fmt, self.width, self.height)
        cr = Context(img)
        strip1 = self.adjust_rgb_for_layer(STRIP1, layer)
        strip2 = self.adjust_rgb_for_layer(STRIP2, layer)
        stripper = GlitchRectBackground(self.width, self.height, strip1, strip2,
                                        0, BACKGROUND_BUMPINESS)
        rects = stripper.get_renderables()
        squarishes = reduce(operator.concat, self.squarishes)
        rects.extend(squarishes)
        for r in rects:
            getattr(r, "render_" + method)(cr)
        return img

    def adjust_rgb_for_layer(self, rgb, layer):
        return (rgb[0] + 0.05 * layer, rgb[1] + 0.065 * layer,
                rgb[2] + 0.1 * layer)


def floor():
    gen = GlitchRectMipMaps(1024, 512, STRIP1, STRIP2, "Floor")
    gen.render_all()
