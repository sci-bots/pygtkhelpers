def find_closest(df_points, point):
    '''
    Parameters
    ----------
    df_points : pandas.DataFrame
        Table with at least ``x`` and ``y`` columns.
    point : pandas.Series
        Series with at least ``x`` and ``y`` keys.

    Returns
    -------
    pandas.Series
        Row of :data:`df_points` table with point closest to specified
        :data:`point`.


    .. versionchanged:: 0.21
        Discontinue use of deprecated ``pandas.Series.argmin``.
    '''
    return df_points.iloc[((df_points - point) ** 2).sum(axis=1).values
                          .argmin()]
