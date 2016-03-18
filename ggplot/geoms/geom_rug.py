from __future__ import (absolute_import, division, print_function)

import numpy as np
import matplotlib.collections as mcoll

from ..utils import to_rgba, make_line_segments
from .geom import geom


class geom_rug(geom):
    DEFAULT_AES = {'alpha': 1, 'color': 'black', 'size': 1.5,
                   'linetype': 'solid'}
    DEFAULT_PARAMS = {'stat': 'identity', 'position': 'identity',
                      'sides': 'bl'}
    legend_geom = 'path'

    @staticmethod
    def draw_group(data, panel_scales, coord, ax, **params):
        data = coord.transform(data, panel_scales)

        has_x = 'x' in data.columns
        has_y = 'y' in data.columns

        if has_x or has_y:
            n = len(data)
        else:
            return

        rugs = []
        sides = params['sides']
        xmin, xmax = panel_scales['x_range']
        ymin, ymax = panel_scales['y_range']
        xheight = (xmax-xmin)*0.03
        yheight = (ymax-ymin)*0.03

        if has_x:
            if 'b' in sides:
                x = np.repeat(data['x'].values, 2)
                y = np.tile([ymin, ymin+yheight], n)
                rugs.extend(make_line_segments(x, y, ispath=False))

            if 't' in sides:
                x = np.repeat(data['x'].values, 2)
                y = np.tile([ymax-yheight, ymax], n)
                rugs.extend(make_line_segments(x, y, ispath=False))

        if has_y:
            if 'l' in sides:
                x = np.tile([xmin, xmin+xheight], n)
                y = np.repeat(data['y'].values, 2)
                rugs.extend(make_line_segments(x, y, ispath=False))

            if 'r' in sides:
                x = np.tile([xmax-xheight, xmax], n)
                y = np.repeat(data['y'].values, 2)
                rugs.extend(make_line_segments(x, y, ispath=False))

        color = to_rgba(data['color'], data['alpha'])
        coll = mcoll.LineCollection(rugs,
                                    edgecolor=color,
                                    linewidth=data['size'],
                                    linestyle=data['linetype'].tolist(),
                                    zorder=params['zorder'])
        ax.add_collection(coll)
