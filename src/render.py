from pygame import Color, Surface

class Renderable:
    """ diffuse and specular are pygame Color values. z is a single float. """
    def __init__(self, diffuse, specular, z):
        self.diffuse = diffuse
        self.specular = specular
        self.z = z

    def render(self, surface, colour):
        raise Exception("render() not implemented")

    def render_diffuse(self, surface):
        self.render(surface, self.diffuse)

    def render_specular(self, surface):
        self.render(surface, self.specular)

    def render_height_map(self, surface):
        cb = int(round(self.z * 255))
        self.render(surface, Color(cb, cb, cb))


class Rect(Renderable):
    def __init__(self, diffuse, specular, z, rect):
        super().__init__(diffuse, specular, z)
        self.rect = rect
        self.x = rect.x
        self.y = rect.y
        self.w = rect.w
        self.h = rect.h

    def render(self, surface, colour):
        surface.fill(colour, self.rect)

    def colliderect(self, r):
        return self.rect.collide(r)

    def collidelist(self, l):
        return self.rect.collidelist(l)
