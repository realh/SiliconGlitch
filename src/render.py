from cairo import Context, Format, ImageSurface

class Renderable:
    """ diffuse and specular are float tuples (r,g,b) or (r,g,b,a),
        z is a single float. """
    def __init__(self, diffuse, specular, z):
        self.diffuse = diffuse
        self.specular = specular
        self.z = z

    def path(self, cr: Context):
        raise Exception("render() not implemented")

    def render(self, cr: Context, colour):
        if len(colour) == 4:
            cr.set_source_rgba(*colour)
        else:
            cr.set_source_rgb(*colour)
        cr.new_path()
        self.path(cr)
        cr.fill()

    def render_diffuse(self, cr: Context):
        self.render(cr, self.diffuse)

    def render_specular(self, cr: Context):
        self.render(cr, self.specular)

    def render_height_map(self, cr: Context):
        self.render(cr, (self.z, self.z, self.z))


class Rect(Renderable):
    def __init__(self, diffuse, specular, z, x, y, w, h):
        super().__init__(diffuse, specular, z)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def path(self, cr: Context):
         cr.rectangle(self.x, self.y, self.w, self.h)
