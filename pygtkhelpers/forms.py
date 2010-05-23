# -*- coding: utf-8 -*-

"""
    pygtkhelpers.forms
    ~~~~~~~~~~~~~~~~~~

    Providing specialized delegates that can be used to map and validate
    against schemas. Validation and schema support is provided by Flatland_.

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

import sys
import gtk

from flatland import Dict, String, Integer, Boolean

from pygtkhelpers.proxy import ProxyGroup, proxy_for
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import gsignal


def _view_type_for_element(element):
    # now do something with element.__class__
    ## something nasty
    bases = (c.__name__ for c in
             [element.__class__] + list(element.__class__.__bases__))
    for base in bases:
        if base in element_views:
            return element_views[base]


def widget_for(element):
    """Create a widget for a schema item
    """
    view_type = _view_type_for_element(element)
    if view_type is None:
        raise KeyError('No view type for %r' % element)
    builder = view_widgets.get(view_type)
    if builder is None:
        raise KeyError('No widget type for %r' % view_type)
    return builder(element)


class Field(object):
    """Encapsulates the widget and the label display
    """

    def __init__(self, element, widget, label_widget=None):
        self.element = element
        self.widget = widget
        self.proxy = proxy_for(widget)
        self.label_widget = gtk.Label()

    def set_label(self, text):
        self.label_widget.set_text(text)

    def _unparent(self):
        self.widget.unparent()
        self.label_widget.unparent()

    def layout_as_table(self, table, row):
        self._unparent()
        self.label_widget.set_alignment(1.0, 0.5)
        table.attach(self.label_widget, 0, 1, row, row+1,
            xoptions=gtk.SHRINK|gtk.FILL, yoptions=gtk.SHRINK)
        table.attach(self.widget, 1, 2, row, row+1,
            xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.SHRINK)





class FieldSet(object):

    def __init__(self, delegate, schema_type):
        self.delegate = delegate
        self.schema = schema_type()
        self.proxies = ProxyGroup()
        self.fields = {}
        self.proxies.connect('changed', self._on_proxies_changed)
        for name, element in self.schema.items():
            self._setup_widget(name, element)

    def _setup_widget(self, name, element):
        widget = getattr(self.delegate, name, None)
        #XXX (AA) this will always be the case, we are running too soon
        if widget is None:
            widget = widget_for(element)
            setattr(self.delegate, name, widget)
        field = self.fields[name] = Field(element, widget=widget)
        field.set_label(name.capitalize())
        self.proxies.add_proxy(name, field.proxy)

    def _on_proxies_changed(self, group, proxy, name, value):
        self.schema[name].set(value)

    def layout_as_table(self):
        table = gtk.Table(len(self.fields), 2)
        table.set_row_spacings(6)
        table.set_col_spacings(6)
        table.set_border_width(6)
        for row, name in enumerate(self.fields):
            self.fields[name].layout_as_table(table, row)
        return table


class FormView(SlaveView):
    """A specialized delegate that adds widget proxying and schema support
    """

    schema_type = None

    def create_ui(self):
        self.form = FieldSet(self, self.schema_type)
        self.widget.pack_start(self.form.layout_as_table())



class WidgetBuilder(object):
    """Defer widget building to allow post-configuration
    """
    def __init__(self, widget_type):
        self.widget_type = widget_type

    def __call__(self, element):
        return self.widget_type()


class IntegerBuilder(object):

    def __call__(self, element):
        render_options = getattr(element, 'render_options', {})
        print element.name, render_options
        style = render_options.get('style', 'spin')
        widget_types = {
            'spin': gtk.SpinButton,
            'slider': gtk.HScale,
        }
        widget = widget_types.get(style)()
        widget.set_digits(0)
        adj = widget.get_adjustment()
        min, max = -sys.maxint, sys.maxint
        for v in element.validators:
            if hasattr(v, 'minimum'):
                min = v.minimum
            elif hasattr(v, 'maximum'):
                max = v.maximum
        adj.set_all(min, min, max, 1.0, 10.0)
        return widget


VIEW_ENTRY = 'entry'
VIEW_PASSWORD = 'password'
VIEW_TEXT = 'text'
VIEW_NUMBER = 'integer'
VIEW_LIST = 'list'
VIEW_CHECK = 'check'

VIEW_LAYOUT_LIST = 'layout-list'
VIEW_LAYOUT_TABLE = 'layout-table'


#: Map of flatland element types to view types
element_views = {
    'String': VIEW_ENTRY,
    'Integer': VIEW_NUMBER,
    'Boolean': VIEW_CHECK,
}

#: map of view types to flatland element types
view_widgets = {
    VIEW_ENTRY: WidgetBuilder(gtk.Entry),
    VIEW_NUMBER: IntegerBuilder(),
    VIEW_CHECK: WidgetBuilder(gtk.CheckButton),
}


