import os
import sys
import pygame
from bumpmap import height_map_to_normals

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
        if img.get_width() != w or img.get_height != h:
            img = pygame.transform.smoothscale(img, (w, h))
        if tchar == 'N':
            img = height_map_to_normals(img)
        d = os.path.abspath(os.path.dirname(sys.argv[0]))
        filename = os.path.join(os.path.dirname(d), "pngs",
                "Stadium%s%s%02d.png" % (self.basename, tchar, layer + 1))
        pygame.image.save(img, filename)
        # H is to save the original heightmap as well as the normal map
        if tchar == 'H':
            self.scale_and_save(img, w, h, layer, 'N')

    def render_layer(self, layer, method, w, h):
        """ Can be overridden to return a cairo Surface. If the result's size
        is different from requested it will be scaled. method is "specular",
        "height_map" or "diffuse". """
        return None
