# -*- coding: utf-8 -*-
from collections import OrderedDict
import logging

from svg_model import svg_polygons_to_df
from svg_model.shapes_canvas import ShapesCanvas
import cairo
import gtk
import pandas as pd

from ...utils import refresh_gui
from .cairo_view import GtkCairoView
from . import composite_surface

logger = logging.getLogger(__name__)


class GtkShapesCanvasView(GtkCairoView):
    def __init__(self, df_shapes, shape_i_columns, padding_fraction=0,
                 **kwargs):
        self.canvas = None
        self.df_shapes = df_shapes
        self.shape_i_columns = shape_i_columns
        self.padding_fraction = padding_fraction
        self._canvas_reset_request = None
        self.cairo_surface = None
        super(GtkShapesCanvasView, self).__init__(**kwargs)

    @classmethod
    def from_svg(cls, svg_filepath, **kwargs):
        df_shapes = svg_polygons_to_df(svg_filepath)
        return cls(df_shapes, 'path_id', **kwargs)

    def create_ui(self):
        super(GtkShapesCanvasView, self).create_ui()
        self.widget.set_events(gtk.gdk.BUTTON_PRESS |
                               gtk.gdk.BUTTON_RELEASE |
                               gtk.gdk.BUTTON_MOTION_MASK |
                               gtk.gdk.BUTTON_PRESS_MASK |
                               gtk.gdk.BUTTON_RELEASE_MASK |
                               gtk.gdk.POINTER_MOTION_MASK)

    def reset_canvas(self, width, height):
        canvas_shape = pd.Series([width, height], index=['width', 'height'])
        self.canvas = ShapesCanvas(self.df_shapes, self.shape_i_columns,
                                   canvas_shape=canvas_shape,
                                   padding_fraction=self.padding_fraction)

    def draw(self):
        if self.cairo_surface is not None:
            logger.debug('Paint canvas on widget Cairo surface.')
            cairo_context = self.widget.window.cairo_create()
            cairo_context.set_source_surface(self.cairo_surface, 0, 0)
            cairo_context.paint()
        else:
            logger.debug('No Cairo surface to paint to.')

    def render(self):
        self.surfaces = OrderedDict()
        self.surfaces['shapes'] = self.render_shapes()
        self.cairo_surface = self.flatten_surfaces()

    def on_canvas_reset_tick(self, shape=None):
        if shape is None:
            width, height = self._canvas_reset_request
        else:
            width, height = shape
        logger.debug('on_canvas_reset_tick')
        self.reset_canvas(width, height)
        logger.debug('on_canvas_reset_tick [canvas reset]')
        def update_gui():
            self.render()
            logger.debug('on_canvas_reset_tick [render complete]')
            self.draw()
            logger.debug('on_canvas_reset_tick [draw complete]')
            self._canvas_reset_request = None
        gtk.idle_add(update_gui)

    def on_widget__configure_event(self, widget, event):
        '''
        Called when size of drawing area changes.
        '''
        if event.x < 0 and event.y < 0:
            # Widget has not been allocated a size yet, so do nothing.
            return
        logger.debug('on_widget__configure_event')
        # Use `self._canvas_reset_request` latch to throttle configure event
        # handling.
        # This makes the UI more responsive when resizing the drawing area, for
        # example, by dragging the window border.
        request_pending = (self._canvas_reset_request is not None)
        self._canvas_reset_request = (event.width, event.height)
        if not request_pending:
            gtk.timeout_add(500, self.on_canvas_reset_tick)

    def on_widget__expose_event(self, widget, event):
        '''
        Called when drawing area is first displayed and, for example, when part
        of drawing area is uncovered after being covered up by another window.
        '''
        logger.debug('on_widget__expose_event')
        # Paint pre-rendered off-screen Cairo surface to drawing area widget.
        self.draw()

    ###########################################################################
    # Render methods
    def render_shapes(self, df_shapes=None, clip=False):
        x, y, width, height = self.widget.get_allocation()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cairo_context = cairo.Context(surface)

        if df_shapes is None:
            df_shapes = self.canvas.df_canvas_shapes

        for path_id, df_path_i in (df_shapes
                                   .groupby(self.canvas
                                            .shape_i_columns)[['x', 'y']]):
            cairo_context.move_to(*df_path_i.iloc[0][['x', 'y']])
            for i, (x, y) in df_path_i[['x', 'y']].iloc[1:].iterrows():
                cairo_context.line_to(x, y)
            cairo_context.close_path()
            cairo_context.set_source_rgb(0, 0, 1)
            cairo_context.fill()
        return surface

    def flatten_surfaces(self, **kwargs):
        '''
        Flatten all surfaces into a single Cairo surface.
        '''
        return composite_surface(self.surfaces.values(), **kwargs)


def parse_args(args=None):
    """Parses arguments, returns (options, args)."""
    import sys
    from argparse import ArgumentParser
    from path_helpers import path

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='Example app for drawing shapes from '
                            'dataframe, scaled to fit to GTK canvas while '
                            'preserving aspect ratio (a.k.a., aspect fit).')
    parser.add_argument('svg_filepath', type=path, default=None)
    parser.add_argument('-p', '--padding-fraction', type=float, default=0)

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_args()
    view = GtkShapesCanvasView.from_svg(args.svg_filepath,
                                        padding_fraction=args.padding_fraction)
    view.widget.connect('destroy', gtk.main_quit)
    view.show_and_run()
