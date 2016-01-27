def find_closest(df_points, point):
    return df_points.iloc[((df_points - point) ** 2).sum(axis=1).argmin()]
