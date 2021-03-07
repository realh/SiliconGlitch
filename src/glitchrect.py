import random
import operator
from functools import reduce
import pygame
from pygame import Color, Surface
import render
from mipmaps import MipMapGenerator
from colour import random_colour

NUM_STRIPS = 16
# I think in TM1/Forever the specular RGB determine what colour it shines,
# alpha is shininess. In TM2 the R and G are used for something else and B is
# zero.
BACKGROUND_SPECULAR1 = 0.25
BACKGROUND_SPECULAR2 = 0.333
BACKGROUND_BUMPINESS = 0.2
FOREGROUND_SPECULAR = 128

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
                s = BACKGROUND_SPECULAR1
            else:
                d = self.strip2
                b = BACKGROUND_BUMPINESS
                s = BACKGROUND_SPECULAR2
            s = Color(d.r, d.g, d.b, int(round(s * 255)))
            strips.append(render.Rect(d, s, b,
                pygame.Rect(n * sw, 0, sw, self.height)))
        return strips


# Squarish blocks are added with dimension limits according to these constants.
RAND_SQ_BASE = 8
RAND_SQ_MIN = 3
RAND_SQ_MAX = 5
RAND_SQ_PADDING = RAND_SQ_BASE / 2


def fill_random_squarishes(rects, width, height):
    """ rects is a list of lists. Each inner list contains 1, 2 or 4 Rects, so
    that rects near edges or corners are duplicated for tilability in an
    eclosing rect of width x height. The outer list may be empty at input. This
    function adds rects until the enclosing space is "fullish". """
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
        group = [pygame.Rect(x, y, w, h)]
        cx = x - RSP
        cy = y - RSP
        cw = w + 2 * RSP
        ch = h + 2 * RSP
        collidables = [pygame.Rect(cx, cy, cw, ch)]
        if x + w > width:
            group.append(pygame.Rect(x - width, y, w, h))
        if cx + cw > width:
            collidables.append(pygame.Rect(cx - width, cy, cw, ch))
        if cx < 0:
            collidables.append(pygame.Rect(cx + width, cy, cw, ch))
        if y + h > height:
            group.append(pygame.Rect(x, y - height, w, h))
            if x + w > width:
                group.append(pygame.Rect(x - width, y - height, w, h))
        if cy + ch > height:
            collidables.append(pygame.Rect(cx, cy - height, cw, ch))
            if cx + cw > width:
                collidables.append(pygame.Rect(cx - width, cy - height, cw, ch))
            if cx < 0:
                collidables.append(pygame.Rect(cx + width, cy - height, cw, ch))
        if cy < 0:
            collidables.append(pygame.Rect(cx, cy + height, cw, ch))
            if cx + cw > width:
                collidables.append(pygame.Rect(cx - width, cy + height, cw, ch))
            if cx < 0:
                collidables.append(pygame.Rect(cx + width, cy + height, cw, ch))
        for og in rects:
            for oldr in og:
                for newr in collidables:
                    if rects_collide(oldr, newr):
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

# pygame's collide test says "except the top+bottom or left+right edges".
# What's that supposed to mean?
def rects_collide(r1, r2):
    return (r1.x <= r2.x + r2.w) and (r1.x + r1.w >= r2.x) and \
        (r1.y <= r2.y + r2.h) and (r1.y + r1.h >= r2.y)


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
            grey = round((0.7 + random.random() * 0.1) * 255)
            spec = self.random_spec(grey)
            grey = (grey, grey, grey, 240)
            for i in range(len(group)):
                r = group[i]
                group[i] = render.Rect(grey, spec, 1,
                        pygame.Rect(r.x, r.y, r.w, r.h))
            j += 1

    def prepare_layer(self, layer, w, h):
        if layer == 0:
            return
        # Remove about a third of the squarishes; this just truncates the list
        # so the other 2/3 will stay in the same place in the whole mipmap
        # chain.
        squarishes = self.squarishes[:len(self.squarishes) * 2 // 3]
        # Change the specular of about a third of remaining squarishes; this
        # time make the changes in random places throught the list so we don't
        # always change the same ones.
        l = len(squarishes)
        for group in squarishes:
            if random.randint(0, 2) == 0:
                spec = self.random_spec(group[0].diffuse[0])
                for sq in group:
                    sq.specular = spec
        # Refill
        fill_random_squarishes(squarishes, self.width, self.height)
        self.add_texture_to_squarishes(squarishes, l)
        self.squarishes = squarishes
        
    def render_layer(self, layer, method, w, h):
        alpha = len(self.strip1) == 4 or method == "specular"
        if alpha:
            flags = pygame.SRCALPHA
        else:
            flags = 0
        img = Surface((self.width, self.height), flags, 32)
        strip1 = self.adjust_rgb_for_layer(STRIP1, layer)
        strip2 = self.adjust_rgb_for_layer(STRIP2, layer)
        stripper = GlitchRectBackground(self.width, self.height, strip1, strip2,
                                        0, BACKGROUND_BUMPINESS)
        rects = stripper.get_renderables()
        squarishes = reduce(operator.concat, self.squarishes)
        rects.extend(squarishes)
        for r in rects:
            getattr(r, "render_" + method)(img)
        return img

    def adjust_rgb_for_layer(self, rgb, layer):
        colour = (round((rgb[0] + 0.025 * layer) * 255),
                  round((rgb[1] + 0.0325 * layer) * 255),
                  round((rgb[2] + 0.05 * layer) * 255))
        try:
            return Color(*colour)
        except:
            print("Bad rgb", rgb, "* layer", layer, ":", colour)
            raise

    def random_spec(self, grey):
        r,g,b = random_colour(0.25, grey)
        # Make sure blue isn't the strongest component, so there's a bit more
        # contrast with the background strips
        if b >= r and b >= g:
            if r < g:
                r, b = b, r
            else:
                b, g = g, b
        return (r,g,b)


def floor():
    gen = GlitchRectMipMaps(1024, 512, STRIP1, STRIP2, "Floor")
    gen.render_all()
