# -*- coding: utf-8 -*-
import gtk
from svg_model import svg_polygons_to_df
import pandas as pd
from svg_model.shapes_canvas import ShapesCanvas
from .cairo_view import GtkCairoView


class GtkShapesCanvasView(GtkCairoView):
    def __init__(self, df_shapes, shape_i_columns, padding_fraction=0,
                 **kwargs):
        self.canvas = None
        self.df_shapes = df_shapes
        self.shape_i_columns = shape_i_columns
        self.padding_fraction = padding_fraction
        self._canvas_reset_request = False
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

    def draw_shapes(self):
        cairo_context = self.widget.window.cairo_create()

        for path_id, df_path_i in (self.canvas.df_canvas_shapes
                                   .groupby(self.canvas
                                            .shape_i_columns)[['x', 'y']]):
            cairo_context.move_to(*df_path_i.iloc[0][['x', 'y']])
            for i, (x, y) in df_path_i[['x', 'y']].iloc[1:].iterrows():
                cairo_context.line_to(x, y)
            cairo_context.close_path()
            cairo_context.set_source_rgb(0, 0, 1)
            cairo_context.fill()

    def on_canvas_reset_tick(self, width, height):
        canvas_shape = pd.Series([width, height], index=['width', 'height'])
        self.canvas = ShapesCanvas(self.df_shapes, self.shape_i_columns,
                                   canvas_shape=canvas_shape,
                                   padding_fraction=self.padding_fraction)
        self._canvas_reset_request = False
        gtk.idle_add(self.widget.queue_draw)
        return False

    def on_widget__configure_event(self, widget, event):
        '''
        Called when size of drawing area changes.
        '''
        if event.x < 0 and event.y < 0:
            # Widget has not been allocated a size yet, so do nothing.
            return
        # Use `self._canvas_reset_request` latch to throttle configure event handling.
        # This makes the UI more responsive when resizing the drawing area, for
        # example, by dragging the window border.
        if not self._canvas_reset_request:
            self._canvas_reset_request = True
            #gtk.timeout_add(50, self.on_canvas_reset_tick, event.width,
                            #event.height)
            gtk.idle_add(self.on_canvas_reset_tick, event.width, event.height)

    def on_widget__expose_event(self, widget, event):
        '''
        Called when drawing area is first displayed and, for example, when part
        of drawing area is uncovered after being covered up by another window.
        '''
        if self.canvas is None:
            return
        # Draw shapes from SVG.
        self.draw_shapes()


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
