from __future__ import absolute_import, division, print_function

from warnings import warn

import pandas as pd
import pandas.api.types as pdtypes
import numpy as np
from patsy.eval import EvalEnvironment
import six

from .ggplot import ggplot
from .aes import aes, all_aesthetics
from .labels import ggtitle, xlab as xlabel, ylab as ylabel
from .facets import facet_null, facet_grid, facet_wrap
from .facets.facet_grid import parse_grid_facets
from .facets.facet_wrap import parse_wrap_facets
from .utils import Registry, is_string, DISCRETE_KINDS, suppress
from .exceptions import PlotnineError
from .scales import scale_x_log10, scale_y_log10
from .themes import theme


def qplot(x=None, y=None, data=None, facets=None, margins=False,
          geom='auto', xlim=None, ylim=None, log='', main=None,
          xlab=None, ylab=None, asp=None, **kwargs):
    """
    Quick plot

    Parameters
    ----------
    x: str | array_like
        x aesthetic
    y: str | array_like
        y aesthetic
    data: pandas.DataFrame
        Data frame to use (optional). If not specified,
        will create one, extracting arrays from the
        current environment.
    geom: str | list
        *geom(s)* to do the drawing. If ``auto``, defaults
        to 'point' if ``x`` and ``y`` are specified or
        'histogram' if only ``x`` is specified.
    xlim: tuple
        x-axis limits
    ylim: tuple
        y-axis limits
    log: 'x' | 'y' | 'xy'
        Which variables to log transform.
    main: str
        Plot title
    xlab: str
        x-axis label
    ylab: str
        y-axis label
    asp: str | float
        The y/x aspect ratio.
    kwargs: dict
        Arguments passed on to the geom.

    Returns
    -------
    p: ggplot
        ggplot object
    """
    # Extract all recognizable aesthetic mappings from the parameters
    # String values e.g  "I('red')", "I(4)" are not treated as mappings

    environment = EvalEnvironment.capture(1)
    aesthetics = {} if x is None else {'x': x}
    if y is not None:
        aesthetics['y'] = y

    def is_mapping(value):
        """
        Return True if value is not enclosed in I() function
        """
        with suppress(AttributeError):
            return not (value.startswith('I(') and value.endswith(')'))
        return True

    def I(value):
        return value

    I_env = EvalEnvironment([{'I': I}])

    for ae in six.viewkeys(kwargs) & all_aesthetics:
        value = kwargs[ae]
        if is_mapping(value):
            aesthetics[ae] = value
        else:
            kwargs[ae] = I_env.eval(value)

    # List of geoms
    if is_string(geom):
        geom = [geom]
    elif isinstance(geom, tuple):
        geom = list(geom)

    if data is None:
        data = pd.DataFrame()

    # Work out plot data, and modify aesthetics, if necessary
    def replace_auto(lst, str2):
        """
        Replace all occurences of 'auto' in with str2
        """
        for i, value in enumerate(lst):
            if value == 'auto':
                lst[i] = str2
        return lst

    if 'auto' in geom:
        if 'sample' in aesthetics:
            replace_auto(geom, 'qq')
        elif y is None:
            # If x is discrete we choose geom_bar &
            # geom_histogram otherwise. But we need to
            # evaluate the mapping to find out the dtype
            env = environment.with_outer_namespace(
                {'factor': pd.Categorical})

            if isinstance(aesthetics['x'], six.string_types):
                try:
                    x = env.eval(aesthetics['x'], inner_namespace=data)
                except Exception:
                    msg = "Could not evaluate aesthetic 'x={}'"
                    raise PlotnineError(msg.format(aesthetics['x']))
            elif not hasattr(aesthetics['x'], 'dtype'):
                x = np.asarray(aesthetics['x'])

            if x.dtype.kind in DISCRETE_KINDS:
                replace_auto(geom, 'bar')
            else:
                replace_auto(geom, 'histogram')

        else:
            if x is None:
                if pdtypes.is_list_like(aesthetics['y']):
                    aesthetics['x'] = range(len(aesthetics['y']))
                    xlab = 'range(len(y))'
                    ylab = 'y'
                else:
                    # We could solve the issue in layer.compute_asthetics
                    # but it is not worth the extra complexity
                    raise PlotnineError(
                        "Cannot infer how long x should be.")
            replace_auto(geom, 'point')

    p = ggplot(aes(**aesthetics), data=data, environment=environment)

    def get_facet_type(facets):
        with suppress(PlotnineError):
            parse_grid_facets(facets)
            return 'grid'

        with suppress(PlotnineError):
            parse_wrap_facets(facets)
            return 'wrap'

        warn("Could not determine the type of faceting, "
             "therefore no faceting.")
        return 'null'

    if facets:
        facet_type = get_facet_type(facets)
        if facet_type == 'grid':
            p += facet_grid(facets, margins=margins)
        elif facet_type == 'wrap':
            p += facet_wrap(facets)
        else:
            p += facet_null()

    # Add geoms
    for g in geom:
        geom_name = 'geom_{}'.format(g)
        geom_klass = Registry[geom_name]
        stat_name = 'stat_{}'.format(geom_klass.DEFAULT_PARAMS['stat'])
        stat_klass = Registry[stat_name]
        # find params
        recognized = (six.viewkeys(kwargs) &
                      (six.viewkeys(geom_klass.DEFAULT_PARAMS) |
                       geom_klass.aesthetics() |
                       six.viewkeys(stat_klass.DEFAULT_PARAMS) |
                       stat_klass.aesthetics()))
        recognized = recognized - six.viewkeys(aesthetics)
        params = {ae: kwargs[ae] for ae in recognized}
        p += geom_klass(**params)

    if 'x' in log:
        p += scale_x_log10()

    if 'y' in log:
        p += scale_y_log10()

    if xlab:
        p += xlabel(xlab)

    if ylab:
        p += ylabel(ylab)

    if main:
        p += ggtitle(main)

    if asp:
        p += theme(aspect_ratio=asp)

    return p
