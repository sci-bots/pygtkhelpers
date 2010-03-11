# -*- coding: utf-8 -*-

"""
    pygtkhelpers.ui.widgets
    ~~~~~~~~~~~~~~~~~~~~~~~

    Miscellaneous additional custom widgets

    :copyright: 2005-2010 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""
import gtk
from pygtkhelpers.utils import gsignal


class StringList(gtk.VBox):

    gsignal('content-changed')

    def __init__(self):
        gtk.VBox.__init__(self, spacing=3)
        self.set_border_width(6)
        self.set_size_request(0, 150)

        self.store = gtk.ListStore(str)
        self.view = gtk.TreeView()
        self.view.set_headers_visible(False)
        self.view.set_model(self.store)
        #XXX: scrollable?
        self.pack_start(self.view, expand=True)

        self.tv_col = gtk.TreeViewColumn()
        self.text_renderer = gtk.CellRendererText()
        self.tv_col.pack_start(self.text_renderer)
        self.tv_col.add_attribute(self.text_renderer, 'text', 0)

        self.view.append_column(self.tv_col)

        selection = self.view.get_selection()
        selection.connect('changed', self._on_selection_changed)

        hb = gtk.HButtonBox()
        self.value_entry = gtk.Entry()
        self.value_entry.connect('changed', self._on_value_changed)
        self.value_entry.set_sensitive(False)
        self.pack_start(self.value_entry, expand=False)
        self.add_button = gtk.Button(stock=gtk.STOCK_NEW)
        self.add_button.connect('clicked', self._on_add)
        hb.pack_start(self.add_button, expand=False)
        self.rem_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.rem_button.connect('clicked', self._on_rem)
        self.rem_button.set_sensitive(False)
        hb.pack_start(self.rem_button, expand=False)
        self.pack_start(hb, expand=False)
        self._current =  None
        self._block = False
        
    def _on_add(self, button):
        iter = self.store.append(["New Item"])
        self.view.get_selection().select_iter(iter)
        self._emit_changed()

    def _on_rem(self, button):
        if self._current:
            self.store.remove(self._current)
            self._current = None
            self.view.get_selection().unselect_all()
        self._emit_changed()

    def _on_selection_changed(self, selection):
        model, iter = selection.get_selected()

        self.rem_button.set_sensitive(iter is not None)
        self._current = iter
        if iter is not None:
            self.value_entry.set_sensitive(True)
            self.value_entry.set_text(model[iter][0])
        else:
            self.value_entry.set_sensitive(False)
            self.value_entry.set_text('')

    def _on_value_changed(self, entry):
        if self._current is  not None:
            self._block = True
            self.store.set(self._current, 0, entry.get_text())
            self._emit_changed()

    def _emit_changed(self) :
        self.emit('content-changed')
        
    def update(self, value):
        if not self._block: 
            self.store.clear()
            for item in value:
                self.store.append([item])
        self._block = False

    def read(self):
        return [i[0] for i in self.store]

    value = property(read, update)



class SimpleComboBox(gtk.ComboBox):
    '''a simple combobox that maps descriptions to keys'''
    __gtype_name__ = 'PyGTKHelpersSimpleComboBox'

    def __init__(self, choices=None, default=None):
        gtk.ComboBox.__init__(self)
        if choices and not default:
            raise ValueError('default choice necessary')
        self.store = gtk.ListStore(str, str)
        self.set_model(self.store)
        if choices is not None:
            self.set_choices(choices, default)

        self.renderer = gtk.CellRendererText()
        self.pack_start(self.renderer, True)
        self.add_attribute(self.renderer, 'text', 0)

    def set_choices(self, choices, default):
        self.store.clear()
        for item in choices:
            iter = self.store.append((item[1], item[0]))
            if item[0] == default:
                self.set_active_iter(iter)




class AttrSortCombo(gtk.HBox):
    """
    A evil utility class that hijacks a objectlist and forces ordering onto its model
    """
    def __init__(self, objectlist, attribute_list, default):
        gtk.HBox.__init__(self, spacing=3)
        self.set_border_width(3)
        from pygtkhelpers.ui.widgets import SimpleComboBox
        from pygtkhelpers.proxy import GtkComboBoxProxy

        self._objectlist = objectlist

        self._combo = SimpleComboBox(attribute_list, default)
        self._proxy = GtkComboBoxProxy(self._combo)
        self._proxy.connect_widget()
        self._proxy.connect('changed', self._on_configuration_changed)
        self._order_button = gtk.ToggleToolButton(
            stock_id=gtk.STOCK_SORT_DESCENDING)
        self._order_button.connect('toggled', self._on_configuration_changed)
        self._label = gtk.Label('Sort')
        self.pack_start(self._label, expand=False)
        self.pack_start(self._combo)
        self.pack_start(self._order_button, expand=False)
        self._on_configuration_changed()
        self.show_all()

    def _on_configuration_changed(self, *k):
        order_descending = self._order_button.get_active()
        if order_descending:
            order = gtk.SORT_DESCENDING
        else:
            order = gtk.SORT_ASCENDING
        attribute = self._proxy.read()

        try:
            self._objectlist.sort_by(attribute, order)
            print 'smart sort', self._objectlist, attribute, order
        except AttributeError:
            print 'broken sort', self._objectlist, attribute, order
            model = self._objectlist.get_model()
            model.set_default_sort_func(_attr_sort_func, attribute)
            model.set_sort_column_id(-1, order)


def _attr_sort_func(model, iter1, iter2 , attribute):
    """internal heloer"""
    attr1 = getattr(model[iter1][0], attribute, None)
    attr2 = getattr(model[iter2][0], attribute, None)
    return cmp(attr1, attr2)

