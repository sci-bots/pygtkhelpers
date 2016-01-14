import cairo


def composite_surface(surfaces, op=cairo.OPERATOR_OVER):
    max_width = max([s.get_width() for s in surfaces])
    max_height = max([s.get_height() for s in surfaces])

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, max_width, max_height)
    surface_context = cairo.Context(surface)

    for surface_i in surfaces:
        surface_context.set_operator(op)
        surface_context.set_source_surface(surface_i)
        surface_context.paint()
    return surface


def find_closest(df_points, point):
    return df_points.iloc[((df_points - point) ** 2).sum(axis=1).argmin()]
