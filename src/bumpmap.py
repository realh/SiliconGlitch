import math
from pygame import Color, PixelArray, Surface, SRCALPHA

def sample_luminance(pix, w, h, x, y):
    """ Gets the value of the G channel in the pixel at (x, y) in data
    representing a w x h surface. x and y wrap around if out of range. 
    The format is assumed to be ARGB32, but we don't care about endianness,
    because it doesn't matter whether we sample blue or green. The result is
    a float 0.0-1.0. """
    if x >= w:
        x -= w
    elif x < 0:
        x += w
    if y >= h:
        y -= h
    elif y < 0:
        y += h
    rgba = pix[x, y]
    return ((rgba >> 16) & 255) / 255


def nc_to_byte(f):
    """ Instead of two's complement, it seems like the standard is to use an
    offset of 128. """
    return int(round(f * 127)) + 128
    

def height_map_to_normals(hm_surf, amp = 20):
    """ hm_surf is a Surface whose pixel values represent heights between
    0 and 1. Only the green (or blue) channel is read. The output consists of
    normals for the surface in R0GzByAx format. amp is a multiplication factor
    for the slope ratios. GIMP's default equivalent for amp is 10, so we might
    as well use that, bearing in mind we also divide by 2 to average 2
    differences across 3 pixels. """
    w = hm_surf.get_width()
    h = hm_surf.get_height()
    hm = PixelArray(hm_surf)
    nm_surf = Surface((w, h), SRCALPHA, 32)
    nm = PixelArray(nm_surf)
    # The slope ratio is the average of two differences (hence / 2): 
    # current - previous and next - current, divided by the distance in the
    # plane (1), then we multiply by amp. So adjust amp to do all of that in
    # one multiplication.
    amp /= 2
    for y in range(h):
        for x in range(w):
            # p gets cancelled out by averaging with p1 and p0
            # p = sample_luminance(hm, w, h, x, y)
            px0 = sample_luminance(hm, w, h, x - 1, y)
            px1 = sample_luminance(hm, w, h, x + 1, y)
            py0 = sample_luminance(hm, w, h, x, y - 1)
            py1 = sample_luminance(hm, w, h, x, y + 1)
            # These should really be called dz/dx and dz/dy
            dx = (px1 - px0) * amp
            dy = (py1 - py0) * -amp # Cairo y is inverted wrt 3D space
            if dx == 0 and dy == 0:
                # Shortcut
                vx = 0
                vy = 0
                vz = 1
            else:
                # This gives us two tangents (1, 0, dx) and (0, 1, dy); the
                # normals are (-dx, 0, 1) and (0, dy, 1); normalise their
                # magnitudes:
                magx = math.sqrt(1 + dx * dx)
                magy = math.sqrt(1 + dy * dy)
                # The 3D normal vector is the addition of these, with its
                # magnitude normalised.
                nx = -dx / magx
                ny = dy / magy
                nz = 1 / magx + 1 / magy
                mag = math.sqrt(nx * nx + ny * ny + nz * nz)
                vx = nx / mag
                vy = ny / mag
                vz = nz / mag
            # Trackmania's swizzled format. ByGzR0Ax.
            rgba = Color(0, nc_to_byte(vz), nc_to_byte(vy), nc_to_byte(vx))
            nm[x, y] = rgba
            # For visual inspection and/or comparison with standard normal map
            # generators, use RxGyBzA1
            #rgba = Color(nc_to_byte(vx), nc_to_byte(vy), nc_to_byte(vz), 255)
    nm.close()
    hm.close()
    return nm_surf
