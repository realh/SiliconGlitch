import math
from cairo import Format, ImageSurface

def sample_luminance(data, w, h, x, y):
    """ Gets the value of the G channel in the pixel at (x, y) in data
    representing a w x h surface. x and y wrap around if out of range. data's
    format is ARGB32 (Cairo's RGB24 is the same with A ignored) stored in
    native endianness. This assumes we're running on a little-endian system,
    which is naughty, but OK because:
    1. In practice I'm never going to run this on a BE system.
    2. The caller is only interested in luminance of greyscale surfaces, so it
       doesn't matter whether we read R when we think we're reading G.
    """
    if x >= w:
        x -= w
    elif x < 0:
        x += w
    if y >= h:
        y -= h
    elif y < 0:
        y += h
    i = (x + y * w) * 4
    return data[i + 1] / 255


def signed_byte(f):
    i = int(round(f * 127))
    if f < 0:
        i = 255 + i
    return i


def height_map_to_normals(hm_surf, amp = 1):
    """ hm_surf is an ImageSurface whose pixel values represent heights between
    0 and 1. Only the green channel is read. The output consists of normals for
    the surface in R0GzByAx format. amp is a multiplication factor for the
    slope ratios. """
    w = hm_surf.get_width()
    h = hm_surf.get_height()
    hm = hm_surf.get_data()
    nm_surf = ImageSurface(Format.ARGB32, w, h)
    nm = nm_surf.get_data()
    # The slope ratio is the average of two differences (hence / 2): 
    # current - previous and next - current, divided by the distance in the
    # plane (1), then we multiply by amp. So adjust amp to do all of that in
    # one multiplication.
    amp /= 2
    i = 0
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
            dy = (py1 - py0) * amp
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
            nm[i] = signed_byte(vy)     # B = y
            nm[i + 1] = signed_byte(vz) # G = z
            nm[i + 2] = 0               # R = 0
            nm[i + 3] = signed_byte(vx) # A = x
            # Use the following values for visual inspection
            #nm[i] = signed_byte(vz)     # B = z
            #nm[i + 1] = signed_byte(vy) # G = y
            #nm[i + 2] = signed_byte(vx) # R = x
            #nm[i + 3] = 255             # A = opaque
            i += 4
    return nm_surf
