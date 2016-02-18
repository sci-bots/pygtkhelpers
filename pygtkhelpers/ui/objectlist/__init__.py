# -*- coding: utf-8 -*-

"""
    pygtkhelpers.ui.objectlist
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    TreeViews that are object orientated, and mimic Pythonic lists

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""
from si_prefix import si_format, si_parse
import numpy as np

from .column import PropertyMapper, Cell, Column
from .view import ObjectList, ObjectTree
from .combined_fields import *


def get_py_dtype(np_dtype):
    '''
    Args:

        np_dtype (numpy.dtype)

    Returns:

        (type) : Python data type that corresponds to the specified numpy
            dtype.
    '''
    if np_dtype.type == np.object_:
        return object
    elif hasattr(np_dtype.type(0), 'item'):
        return type(np_dtype.type(0).item())
    else:
        return type(np_dtype.type(0))


def get_py_dtypes(data_frame):
    '''
    Return a `pandas.DataFrame` containing Python type information for the
    columns in `data_frame`.

    Args:

        data_frame (pandas.DataFrame) : Data frame containing data columns.

    Returns:

        (pandas.DataFrame) : Data frame indexed by the column names from
            `data_frame`, with the columns `'i'` and `'dtype'` indicating the
            index and Python type of the corresponding `data_frame` column,
            respectively.
    '''
    df_py_dtypes = data_frame.dtypes.map(get_py_dtype).to_frame('dtype').copy()
    df_py_dtypes.loc[df_py_dtypes.dtype == object, 'dtype'] = \
        (df_py_dtypes.loc[df_py_dtypes.dtype == object].index
         .map(lambda c: str if data_frame[c]
              .map(lambda v: isinstance(v, str)).all() else object))

    df_py_dtypes.insert(0, 'i', range(df_py_dtypes.shape[0]))
    df_py_dtypes.index.name = 'column'
    return df_py_dtypes


def get_list_store(data_frame):
    '''
    Return a `pandas.DataFrame` containing Python type information for the
    columns in `data_frame` and a `gtk.ListStore` matching the contents of the
    data frame.

    Args:

        data_frame (pandas.DataFrame) : Data frame containing data columns.

    Returns:

        (tuple) : The first element is a data frame as returned by
            `get_py_dtypes` and the second element is a `gtk.ListStore`
            matching the contents of the data frame.
    '''
    df_py_dtypes = get_py_dtypes(data_frame)
    list_store = gtk.ListStore(*df_py_dtypes.dtype)
    for i, row_i in data_frame.iterrows():
        list_store.append(row_i.tolist())
    return df_py_dtypes, list_store


def add_columns(tree_view, df_py_dtypes, list_store):
    '''
    Add columns to a `gtk.TreeView` for the types listed in `df_py_dtypes`.

    Args:

        tree_view (gtk.TreeView) : Tree view to append columns to.
        df_py_dtypes (pandas.DataFrame) : Data frame containing type
            information for one or more columns in `list_store`.
        list_store (gtk.ListStore) : Model data.

    Returns:

        None
    '''
    tree_view.set_model(list_store)

    for column_i, (i, dtype_i) in df_py_dtypes[['i', 'dtype']].iterrows():
        tree_column_i = gtk.TreeViewColumn(column_i)
        tree_column_i.set_name(column_i)
        if dtype_i in (int, long):
            property_name = 'text'
            cell_renderer_i = gtk.CellRendererSpin()
        elif dtype_i == float:
            property_name = 'text'
            cell_renderer_i = gtk.CellRendererSpin()
        elif dtype_i in (bool, ):
            property_name = 'active'
            cell_renderer_i = gtk.CellRendererToggle()
        elif dtype_i in (str, ):
            property_name = 'text'
            cell_renderer_i = gtk.CellRendererText()
        else:
            raise ValueError('No cell renderer for dtype: %s' % dtype_i)
        cell_renderer_i.set_data('column_i', i)
        cell_renderer_i.set_data('column', tree_column_i)
        tree_column_i.pack_start(cell_renderer_i, True)
        tree_column_i.add_attribute(cell_renderer_i, property_name, i)
        tree_view.append_column(tree_column_i)


def set_column_format(tree_column, model_column_index, format_str,
                      cell_renderer=None):
    '''
    Set the text of a cell according to a [format][1] string.

    [1]: https://docs.python.org/2/library/string.html#formatstrings

    Args:

        tree_column (gtk.TreeViewColumn) : Tree view to append columns to.
        model_column_index (int) : Index in list store model corresponding to
            tree view column.
        format_str (str) : Format string as accepted by Python string `format`
            method (e.g., `'{value}'`).  N.B., the value of a cell is passed to
            the `format` method as a keyword argument.
        cell_renderer (gtk.CellRenderer) : Cell renderer for column.  If
            `None`, defaults to all cell renderers for column.

    Returns:

        None
    '''
    def set_property(column, cell_renderer, list_store, iter, store_i):
        value = list_store[iter][store_i]
        cell_renderer.set_property('text', format_str.format(value=value))
    if cell_renderer is None:
        cells = tree_column.get_cells()
    else:
        cells = [cell_renderer]
    for cell_renderer_i in cells:
        tree_column.set_cell_data_func(cell_renderer_i, set_property,
                                       model_column_index)


def set_column_si_format(tree_column, model_column_index, cell_renderer=None,
                         digits=2):
    '''
    Set the text of a numeric cell according to [SI prefixes][1]

    For example, `1000 -> '1.00k'`.

    [1]: https://en.wikipedia.org/wiki/Metric_prefix#List_of_SI_prefixes

    Args:

        tree_column (gtk.TreeViewColumn) : Tree view to append columns to.
        model_column_index (int) : Index in list store model corresponding to
            tree view column.
        cell_renderer (gtk.CellRenderer) : Cell renderer for column.  If
            `None`, defaults to all cell renderers for column.
        digits (int) : Number of digits after decimal (default=2).

    Returns:

        None
    '''
    def set_property(column, cell_renderer, list_store, iter, store_i):
        cell_renderer.set_property('text', si_format(list_store[iter][store_i],
                                                     digits))
    if cell_renderer is None:
        cells = tree_column.get_cells()
    else:
        cells = [cell_renderer]
    for cell_renderer_i in cells:
        tree_column.set_cell_data_func(cell_renderer_i, set_property,
                                       model_column_index)


def on_edited_dataframe_sync(cell_renderer, iter, new_value, column,
                             df_py_dtypes, list_store, df_data):
    '''
    Handle the `'edited'` signal from a `gtk.CellRenderer` to:

     * Update the corresponding entry in the list store.
     * Update the corresponding entry in the provided data frame instance.

    The callback can be connected to the cell renderer as follows:

        cell_renderer.connect('edited', on_edited_dataframe_sync, column,
                              list_store, df_py_dtypes, df_data)

    where `column` is the `gtk.TreeViewColumn` the cell renderer belongs to,
    and `df_py_dtypes` and `list_store` are the return values from calling
    `get_list_store` on the `df_data` data frame.

    Args:

        cell_renderer (gtk.CellRenderer)
        iter (str) : Gtk TreeView iterator
        new_value (str) : New value resulting from edit operation.
        column (gtk.TreeViewColumn) : Column containing edited cell.
        df_py_dtypes (pandas.DataFrame) : Data frame containing type
            information for columns in tree view (and `list_store`).
        list_store (gtk.ListStore) : Model containing data bound to tree view.
        df_data (pandas.DataFrame) : Data frame containing data in `list_store`.

    Returns:

        None
    '''
    # Extract name of column (name of TreeView column must match data frame
    # column name).
    column_name = column.get_name()
    # Look up the list store column index and data type for column.
    i, dtype = df_py_dtypes.ix[column_name]
    # Update the list store with the new value.
    if dtype == float:
        value = si_parse(new_value)
    elif dtype == bool:
        value = not list_store[iter][i]

    if value == list_store[iter][i]:
        # Value has not changed.
        return False
    list_store[iter][i] = value
    # Update the data frame with the new value.
    df_data[column_name].values[int(iter)] = value
    return True
