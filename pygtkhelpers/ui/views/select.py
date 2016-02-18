import os

from ...delegates import SlaveView
from ..objectlist import (get_list_store, add_columns,
                          on_edited_dataframe_sync)


class ListSelect(SlaveView):
    builder_path = os.path.join(os.path.dirname(__file__), 'glade',
                                'list_select.glade')

    def __init__(self, df_data=None):
        self.df_data = df_data
        super(ListSelect, self).__init__()

    def create_ui(self):
        super(ListSelect, self).create_ui()

        self.button_select_none.connect('clicked', lambda *args:
                                        self.select_none())
        self.button_select_all.connect('clicked', lambda *args:
                                       self.select_all())

        if self.df_data is not None:
            self.set_data(self.df_data)

    def set_data(self, df_data, select_column='select'):
        self.select_column = select_column
        self.df_data = df_data

        for column in self.treeview_select.get_columns():
            self.treeview_select.remove_column(column)

        self.df_py_dtypes, self.list_store = get_list_store(df_data)
        add_columns(self.treeview_select, self.df_py_dtypes, self.list_store)

        # Keep selected state in `select` data frame column synced with UI.
        select_column = self.treeview_select.get_column(self.df_py_dtypes
                                                        .ix[select_column].i)
        cell = select_column.get_cell_renderers()[0]
        cell.connect('toggled', on_edited_dataframe_sync, None, select_column,
                     self.df_py_dtypes, self.list_store, self.df_data)

    def set_all(self, value):
        column_i = self.df_py_dtypes.ix[self.select_column].i
        select_column = self.treeview_select.get_column(column_i)

        self.df_data.loc[:, select_column] = value
        for i in xrange(len(self.list_store)):
            self.list_store[i][column_i] = value

    def select_none(self):
        self.set_all(False)

    def select_all(self):
        self.set_all(True)
