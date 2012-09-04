# -*- coding: utf-8 -*-

"""
    pygtkhelpers.forms
    ~~~~~~~~~~~~~~~~~~

    Providing specialized delegates that can be used to map and validate
    against schemas. Validation and schema support is provided by Flatland_.


    .. _Flatland: http://discorporate.us/projects/flatland/

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

import sys
import gtk

from flatland import Dict, String, Integer, Boolean, Enum

from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import gsignal


def _view_type_for_element(element):
    # now do something with element.__class__
    ## something nasty
    for element_type in element.__class__.__mro__:
        if element_type in element_views:
            return element_views[element_type]


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
        from pygtkhelpers.proxy import ProxyGroup, proxy_for
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
        # XXX: turn to utility function
        self._unparent()
        self.label_widget.set_alignment(1.0, 0.5)
        table.attach(self.label_widget, 0, 1, row, row+1,
            xoptions=gtk.SHRINK|gtk.FILL, yoptions=gtk.SHRINK)
        table.attach(self.widget, 1, 2, row, row+1,
            xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.SHRINK)




# XXX AA: Needs splitting into view component, and controller component
class FieldSet(object):
    def __init__(self, delegate, schema_type):
        from pygtkhelpers.proxy import ProxyGroup, proxy_for
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
        field_name = element.properties.get('label', name)
        field.set_label(field_name.capitalize())
        self.proxies.add_proxy(name, field.proxy)

    def _on_proxies_changed(self, group, proxy, name, value):
        self.schema[name].set(value)

    def layout_as_table(self):
        # XXX: turn to utility function
        table = gtk.Table(len(self.fields), 2)
        table.set_row_spacings(6)
        table.set_col_spacings(6)
        table.set_border_width(6)
        for row, name in enumerate(self.fields):
            self.fields[name].layout_as_table(table, row)
        return table


class FormView(SlaveView):
    #XXX: helper, dont use for complex
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


class ElementBuilder(object):

    default_style = None

    styles = {}

    def __call__(self, element):
        options = getattr(element, 'render_options', {})
        style = options.get('style', self.default_style)
        widget_type = self.styles.get(style)
        if widget_type is None:
            raise NotImplementedError(element)
        widget = widget_type()
        return self.build(widget, style, element, options)

    def build(self, widget, style, element, options):
        raise NotImplementedError


class BooleanBuilder(ElementBuilder):

    default_style = 'check'

    styles = {
        'check': gtk.CheckButton,
        'toggle': gtk.ToggleButton
    }

    def build(self, widget, style, element, options):
        if style == 'toggle':
            widget.connect('toggled', self._on_toggle_toggled)
            widget.set_use_stock(True)
            self._on_toggle_toggled(widget)
        return widget

    def _on_toggle_toggled(self, toggle):
        if toggle.get_active():
            toggle.set_label(gtk.STOCK_YES)
        else:
            toggle.set_label(gtk.STOCK_NO)


class StringBuilder(ElementBuilder):

    default_style = 'uniline'

    styles = {
        'uniline': gtk.Entry,
        'multiline': gtk.TextView,
    }

    def build(self, widget, style, element, options):
        if style == 'multiline':
            widget.set_size_request(-1, 100)
        return widget


class IntegerBuilder(ElementBuilder):

    default_style = 'spin'

    styles = {
        'spin': gtk.SpinButton,
        'slider': gtk.HScale,
    }

    def build(self, widget, style, element, options):
        widget.set_digits(0)
        adj = widget.get_adjustment()
        min, max = -sys.maxint, sys.maxint
        for v in element.validators:
            if hasattr(v, 'minimum'):
                min = v.minimum
            elif hasattr(v, 'maximum'):
                max = v.maximum
        step = element.properties.get('step', 1.0)
        page_step = element.properties.get('page_step', step * 10)
        adj.set_all(min, min, max, step, page_step)
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
    String: VIEW_ENTRY,
    Integer: VIEW_NUMBER,
    Boolean: VIEW_CHECK,
}

#: map of view types to flatland element types
view_widgets = {
    VIEW_ENTRY: StringBuilder(),
    VIEW_NUMBER: IntegerBuilder(),
    VIEW_CHECK: BooleanBuilder(),
}


