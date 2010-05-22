# -*- coding: utf-8 -*-

"""
    pygtkhelpers.forms
    ~~~~~~~~~~~~~~~~~~

    Providing specialized delegates that can be used to map and validate
    against schemas. Validation and schema support is provided by Flatland_.

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk

from flatland import Dict, String, Integer, Boolean

from pygtkhelpers.proxy import ProxyGroup
from pygtkhelpers.delegates import SlaveView


def _view_type_for_element(element):
    # now do something with element.__class__
    ## something nasty
    bases = [element.__class__] + list(element.__class__.__bases__)
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


class Field(SlaveView):

    def __init__(self, widget=None, label=None):
        self.field_widget = widget
        self.label_widget = label
        SlaveView.__init__(self)


class FormView(SlaveView):
    """A specialized delegate that adds widget proxying and schema support
    """

    schema_type = None

    def __init__(self):
        self.schema = self.schema_type()
        self.proxies = ProxyGroup()
        SlaveView.__init__(self)
        for name, element in self.schema.items():
            self._setup_widget(name, element)

    def _setup_widget(self, name, element):
        widget = getattr(self, name, None)
        if widget is None:
            widget = widget_for(element)
            setattr(self, name, widget)
        self.proxies.add_proxy_for(name, widget)

    def on_proxies__changed(self, group, proxy, name, value):
        self.schema[name].set(value)


class WidgetBuilder(object):
    """Defer widget building to allow post-configuration
    """
    def __init__(self, widget_type):
        self.widget_type = widget_type

    def __call__(self, element):
        return self.widget_type()


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
    String: VIEW_ENTRY,
    Integer: VIEW_NUMBER,
    Boolean: VIEW_CHECK,
}

#: map of view types to flatland element types
view_widgets = {
    VIEW_ENTRY: WidgetBuilder(gtk.Entry),
    VIEW_NUMBER: WidgetBuilder(gtk.SpinButton),
    VIEW_CHECK: WidgetBuilder(gtk.CheckButton),
}


