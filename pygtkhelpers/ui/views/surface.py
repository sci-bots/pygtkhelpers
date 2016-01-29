import os

import gtk
import pandas as pd

from ...utils import gsignal
from ...delegates import SlaveView
from ..objectlist import (get_list_store, add_columns,
                          on_edited_dataframe_sync, set_column_format)


class LayerAlphaController(SlaveView):
    # Emit signal when layer alpha has changed (layer name, alpha).
    gsignal('alpha-changed', str, float)
    # Emit signal when order of layers has changed (list of reordered row
    # indices).
    gsignal('layers-reordered', object)

    builder_path = os.path.join(os.path.dirname(__file__), 'glade',
                                'layers.glade')

    def create_ui(self):
        super(LayerAlphaController, self).create_ui()
        self.treeview_layers.set_reorderable(True)
        self.adjustment_alpha = self._builder.get_object('adjustment_alpha')

    def on_edited(self, cell_renderer, iter, new_value, column, df_py_dtypes,
                  list_store, df_data):
        if on_edited_dataframe_sync(cell_renderer, iter, new_value, column,
                                    df_py_dtypes, list_store, df_data):
            surface_name, alpha = self.df_surfaces.iloc[int(iter)]
            self.adjustment_alpha.set_value(alpha * 100)
            self.emit('alpha-changed', surface_name, alpha)

    def on_treeview_layers__cursor_changed(self, treeview):
        # As a workaround for an apparent race condition, use `idle_add`
        # callback here to give the tree view selection instance to update.
        #
        # *N.B.*, Without doing this, sometimes the previously selected row is
        # still returned by `get_selected()`/`get_selected_rows()`.
        gtk.idle_add(self.set_scale_alpha_from_selection)

    def on_adjustment_alpha__value_changed(self, adjustment):
        #  1. Look up selected layer.
        selection = self.treeview_layers.get_selection()
        list_store, selected_iter = selection.get_selected()
        if selected_iter is None:
            # No layer selected (nothing to do).
            return
        else:
            surface_name, alpha = list_store[selected_iter]
        new_alpha = adjustment.get_value() / 100.

        #  2. Set alpha in `self.df_surfaces` and `self.list_store`.
        self.set_alpha(surface_name, new_alpha)

    def on_button_show__clicked(self, button):
        self.set_alpha_for_selection(1.)

    def on_button_hide__clicked(self, button):
        self.set_alpha_for_selection(0.)

    def set_surfaces(self, df_surfaces):
        '''
        Reset the contents of the tree view to show one row per surface, with
        a column containing the alpha multiplier for the corresponding surface
        (in the range [0, 1]), indexed by surface name.

        For example:

            | index  | alpha  |
            |--------|--------|
            | layer1 | 1.00   |
            | layer2 | 0.65   |
            | ...    | ...    |
        '''
        for column in self.treeview_layers.get_columns():
            self.treeview_layers.remove_column(column)

        self.df_surfaces = pd.DataFrame(df_surfaces.index.values,
                                        columns=[df_surfaces.index.name or
                                                 'index'],
                                        index=df_surfaces.index)

        if 'alpha' in df_surfaces:
            self.df_surfaces['alpha'] = df_surfaces.alpha.copy()
        else:
            self.df_surfaces['alpha'] = 1.

        self.df_py_dtypes, self.list_store = get_list_store(self.df_surfaces)
        add_columns(self.treeview_layers, self.df_py_dtypes, self.list_store)

        self._inserted_row_path = None

        # Adjustment for alpha multiplier for each surface.
        adjustment = gtk.Adjustment(1, 0, 1, .01, .1, 0)
        column = [c for c in self.treeview_layers.get_columns()
                  if c.get_name() == 'alpha'][0]
        cell_renderer = column.get_cells()[0]
        cell_renderer.set_properties(digits=2, editable=True,
                                     adjustment=adjustment)
        cell_renderer.connect('edited', self.on_edited, column,
                              self.df_py_dtypes, self.list_store,
                              self.df_surfaces)
        set_column_format(column, self.df_py_dtypes.ix['alpha'].i,
                          '{value:.2f}', cell_renderer=cell_renderer)
        # Bind handlers for reordering of surface layers.
        for k in ('inserted', 'deleted'):
            self.list_store.connect('row-' + k, getattr(self, 'on_row_' + k))

    def on_row_inserted(self, list_store, row_path, row_iter):
        self._inserted_row_path = row_path[0]

    def on_row_deleted(self, list_store, row_path):
        rows_index = range(self.df_surfaces.shape[0])
        if self._inserted_row_path is not None:
            source_index = row_path[0]
            target_index = self._inserted_row_path
            if source_index > target_index:
                source_index -= 1
            elif source_index < target_index:
                target_index -= 1
        else:
            source_index = row_path[0]
            target_index = None
        rows_index.remove(source_index)
        if target_index is not None:
            rows_index.insert(target_index, source_index)
        self.df_surfaces = self.df_surfaces.take(rows_index, is_copy=False)
        self.emit('layers-reordered', rows_index)

    def set_scale_alpha_from_selection(self):
        '''
        Set scale marker to alpha for selected layer.
        '''
        #  1. Look up selected layer.
        selection = self.treeview_layers.get_selection()
        list_store, selected_iter = selection.get_selected()

        # 2. Set adjustment to current alpha value for selected layer (if any).
        if selected_iter is None:
            # No layer was selected, so disable scale widget.
            self.adjustment_alpha.set_value(100)
            self.scale_alpha.set_sensitive(False)
            return
        else:
            surface_name, alpha = list_store[selected_iter]
            self.adjustment_alpha.set_value(alpha * 100)
            self.scale_alpha.set_sensitive(True)

    def set_alpha_for_selection(self, alpha):
        '''
        Set alpha for selected layer.
        '''
        #  1. Look up selected layer.
        selection = self.treeview_layers.get_selection()
        list_store, selected_iter = selection.get_selected()

        # 2. Set alpha value for layer (if selected).
        if selected_iter is None:
            # No layer was selected, so disable scale widget.
            return
        else:
            surface_name, original_alpha = list_store[selected_iter]

            self.set_alpha(surface_name, alpha)
            self.set_scale_alpha_from_selection()

    def set_alpha(self, surface_name, alpha):
        #  1. Set alpha in `self.df_surfaces`.
        self.df_surfaces.loc[surface_name, 'alpha'] = alpha

        #  2. Set alpha in list store model.
        store_name_column_index = self.df_py_dtypes.iloc[0].i
        store_alpha_column_index = self.df_py_dtypes.ix['alpha'].i

        for row in self.list_store:
            if row[store_name_column_index] == surface_name:
                row[store_alpha_column_index] = alpha
                break

        #  3. Emit `alpha-changed`.
        self.emit('alpha-changed', surface_name, alpha)
