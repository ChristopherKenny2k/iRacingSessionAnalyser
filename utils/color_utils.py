"""Small, stateless colour helpers shared across the Tyre and Fuel pages.

These were previously duplicated as methods on the main window class -
pulling them out here means both pages import the exact same
implementation instead of each carrying their own copy.
"""


def interpolate_color(color1, color2, ratio):
    """Linearly interpolate between two '#rrggbb' hex colours."""
    c1 = [int(color1[i:i + 2], 16) for i in (1, 3, 5)]
    c2 = [int(color2[i:i + 2], 16) for i in (1, 3, 5)]

    r = int(c1[0] + (c2[0] - c1[0]) * ratio)
    g = int(c1[1] + (c2[1] - c1[1]) * ratio)
    b = int(c1[2] + (c2[2] - c1[2]) * ratio)

    return f'#{r:02x}{g:02x}{b:02x}'


def get_tyre_temp_color(temp):
    """Map a tyre temperature to a blue -> teal -> green -> yellow -> orange -> red
    the wider range is used since optimal tyre temps
    can vary fairly considerable across car classes
    again, similar to fuel density (L to Kg conversion), ideally I will implement a more robust 'optimal' tyre range based off specific vehicle loaded into software
    """
    if temp < 50:
        return '#0ea5e9'
    elif temp < 65:
        ratio = (temp - 50) / 15
        return interpolate_color('#0ea5e9', '#14b8a6', ratio)
    elif temp < 80:
        ratio = (temp - 65) / 15
        return interpolate_color('#14b8a6', '#22c55e', ratio)
    elif temp < 90:
        ratio = (temp - 80) / 10
        return interpolate_color('#22c55e', '#eab308', ratio)
    elif temp < 100:
        ratio = (temp - 90) / 10
        return interpolate_color('#eab308', '#f97316', ratio)
    elif temp < 110:
        ratio = (temp - 100) / 10
        return interpolate_color('#f97316', '#ef4444', ratio)
    else:
        return '#ef4444'


def brighten_color(hex_color, factor):
    #Brighten  on hover
    rgb = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    rgb = [min(255, int(c * factor)) for c in rgb]
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
