import os
import sys
from cairo import Context, Format, ImageSurface

class MipMapGenerator:
    """ A MipMapGenerator is the abstract base for a class that can generate
    multiple layers of diffuse, specular and heightmap images for a texture. """
    def __init__(self, width, height, basename):
        """ width and height are the size of the largest layer. basename
        excludes path and "Stadium" prefix, but excludes layer number and
        '.png'. """
        self.width = width
        self.height = height
        self.basename = basename

    def render_all(self):
        w = self.width
        h = self.height
        layer = 0
        while w >= 1 and h >= 1:
            self.prepare_layer(layer, w, h)
            self.scale_and_save(self.render_layer(layer, "diffuse", w, h),
                                w, h, layer, 'D')
            self.scale_and_save(self.render_layer(layer, "specular", w, h),
                                w, h, layer, 'S')
            self.scale_and_save(self.render_layer(layer, "height_map", w, h),
                                w, h, layer, 'N')
            if w == 1 and h == 1:
                break
            if w > 1:
                w //= 2
            if h > 1:
                h //= 2
            layer += 1

    def scale_and_save(self, img, w, h, layer, tchar):
        """ tchar is 'D', 'S', or 'N'. """
        if img == None:
            return
        img = self.resize(img, w, h)
        # TODO: N should be converted from height map to normals
        d = os.path.abspath(os.path.dirname(sys.argv[0]))
        filename = os.path.join(os.path.dirname(d), "pngs",
                "Stadium%s%s%02d.png" % (self.basename, tchar, layer + 1))
        img.write_to_png(filename)

    def resize(self, img, w, h):
        if img == None or (img.get_width() == w or img.get_height() == h):
            return img
        new_img = img.create_similar(img.get_content(), w, h)
        cr = Context(new_img)
        cr.scale(w / img.get_width(), h / img.get_height())
        cr.set_source_surface(img, 0, 0)
        cr.paint()
        return new_img

    def render_layer(self, layer, method, w, h):
        """ Can be overridden to return a cairo Surface. If the result's size
        is different from requested it will be scaled. method is "specular",
        "height_map" or "diffuse". """
        return None
