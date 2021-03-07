from math import sqrt
from random import shuffle, uniform

def random_colour(min_sat, brightness):
    """ Generates a random colour as (r,g,b). min_sat is minimum saturation,
    where 1 means two channels are 0, 0 means grey. brightness is also 0-1.
    The calculations are somewhat simplified, so these targets might not be
    met correctly; brightness is the V of HSV. """
    # To calculate HSV from RGB:
    # Xmax = max(c1, c2, c3) = V
    # Xmin = min(c1, c2, c3) = V - C
    # C = Xmax - Xmin
    # S = C / V
    # S <= Xmax - Xmin
    # Xmin <= Xmax - S
    # To meet saturation target S, Xmax must be between S and 1
    # and other two must be between 0 and Xmax - S.
    c1 = uniform(min_sat, 1)
    c2 = uniform(0, c1 - min_sat)
    c3 = uniform(0, c1 - min_sat)
    # These values should be scaled by brightness
    rgb = [c1 * brightness, c2 * brightness, c3 * brightness]
    # Shuffle, otherwise red would always be strongest
    shuffle(rgb)
    return rgb
