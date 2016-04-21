"""
Copyright 2012 Ryan Fobel and Christian Fobel

This file is part of Microdrop.

Microdrop is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Microdrop is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Microdrop.  If not, see <http://www.gnu.org/licenses/>.
"""
from collections import OrderedDict

from path_helpers import path
import gtk

from ..forms import FormView


script_dir = path(__file__).abspath().parent


def create_form_view(form, values=None, use_markup=True):
    FormView.schema_type = form
    form_view = FormView()
    for field_i in form_view.form.schema.field_schema:
        name_i = field_i.name
        form_field_i = form_view.form.fields[name_i]
        if values:
            value = values[name_i]
        else:
            value = form_field_i.element.default_value
        if not form_field_i.element.set(value):
            raise ValueError('"%s" is not a valid value for field "%s"' %
                             (value, name_i))
        form_field_i.proxy.set_widget_value(value)
        if hasattr(form_field_i.widget, 'set_activates_default'):
            form_field_i.widget.set_activates_default(gtk.TRUE)
        form_field_i.label_widget.set_use_markup(use_markup)
    return form_view


class FormViewDialog(object):
    default_parent = None

    def __init__(self, form_class, title=None, parent=None):
        self.title = title
        self.parent = parent
        self.form_class = form_class

    def create_ui(self):
        builder = gtk.Builder()
        builder.add_from_file(script_dir.joinpath('glade',
                                                  'form_view_dialog.glade'))
        self.window = builder.get_object('form_view_dialog')
        self.vbox_form = builder.get_object('vbox_form')
        if self.title:
            self.window.set_title(self.title)
        if self.parent is None:
            self.parent = self.default_parent
        self.window.set_default_response(gtk.RESPONSE_OK)
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        if self.parent:
            self.window.set_transient_for(self.parent)
        self.window.show_all()

    def create_form_view(self, values=None, use_markup=True):
        self.form_view = create_form_view(self.form_class, values=values,
                                          use_markup=use_markup)

    def run(self, values=None, parent=None, use_markup=True):
        self.create_ui()
        self.create_form_view(values=values, use_markup=use_markup)
        self.form_view.connect('changed', self.on_changed)
        self.form_view.widget.show_all()
        self.vbox_form.pack_start(self.form_view.widget)
        response = self.window.run()
        self.window.destroy()
        return ((response == 0),
                OrderedDict([(name, f.element.value)
                             for name, f in
                             self.form_view.form.fields.items()]))

    def on_changed(self, form_view, proxy_group, proxy, field_name, new_value):
        pass
