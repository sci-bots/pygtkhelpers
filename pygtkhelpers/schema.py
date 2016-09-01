from collections import OrderedDict
import logging
import types

from flatland import Boolean, Enum, Float, Form, Integer, String
from flatland.validation import ValueAtLeast, ValueAtMost
from redirect_io import nostderr
import gtk
import jsonschema
import pandas as pd

from .ui.form_view_dialog import FormViewDialog, create_form_view

logger = logging.getLogger(__name__)


class Skip(Exception):
    pass


def expand_items(form_values, sep='.'):
    '''
    Parameters
    ----------
    form_values : list
        List of ``(key, value)`` tuples, where ``key`` corresponds to the
        ancestor keys of the respective value joined by ``'.'``.  For example,
        the key ``'a.b.c'`` would be expanded to the dictionary
        ``{'a': {'b': {'c': 'foo'}}}``.

    Returns
    -------
    dict
        Nested dictionary, where levels are inferred from each key by splitting
        on ``'.'``.
    '''
    output = {}
    for keys_str_i, value_i in form_values:
        keys_i = keys_str_i.split(sep)
        parents_i = keys_i[:-1]
        fieldname_i = keys_i[-1]

        dict_j = output
        for key_j in parents_i:
            dict_j = dict_j.setdefault(key_j,  {})
        dict_j[fieldname_i] = value_i
    return output


def fields_frame_to_flatland_form_class(df_fields, sep='.'):
    # Create Flatland form class from jsonschema schema.
    return Form.of(*[get_flatland_field(row).named(sep.join(row.parents +
                                                            (row.field, )))
                     for i, row in df_fields.iterrows()])


def flatten_dict(root, parents=None, sep='.'):
    '''
    Args:

        root (dict) : Nested dictionary (e.g., JSON object).
        parents (list) : List of ancestor keys.

    Returns
    -------
    list
        List of ``(key, value)`` tuples, where ``key`` corresponds to the
        ancestor keys of the respective value joined by ``'.'``.  For example,
        for the item in the dictionary ``{'a': {'b': {'c': 'foo'}}}``, the
        joined key would be ``'a.b.c'``.

    See also :func:`expand_items`.
    '''
    if parents is None:
        parents = []

    result = []
    for i, (k, v) in enumerate(root.iteritems()):
        parents_i = parents + [k]
        key_i = sep.join(parents_i)
        if isinstance(v, dict):
            value_i = flatten_dict(v, parents=parents_i, sep=sep)
            result.extend(value_i)
        else:
            value_i = v
            result.append((key_i, value_i))
    return result


def flatten_form(form_instance):
    return OrderedDict([(name_i, field_i.default if field_i.value is None
                         else field_i.value)
                        for name_i, field_i in form_instance.iteritems()])


def get_fields_frame(schema):
    '''
    Args:

        schema (dict) : `JSON schema <http://spacetelescope.github.io/understanding-json-schema/>`_.
    '''
    fields = []

    def get_field_record(i, key, value, parents):
        if value.get('private') or 'default' not in value:
            raise Skip
        field = (len(parents) - 1, i, tuple(parents[:-1]), parents[-1],
                 value['type'], value['default'])
        return fields.append(field)

    # Fill fields list.
    get_types(schema['properties'], get_field_record)

    # Order by level, then explicit index.
    df_fields = pd.DataFrame(sorted(fields), columns=['level_i', 'field_i',
                                                      'parents', 'field',
                                                      'field_type', 'default'])

    df_fields['attributes'] = df_fields.apply(lambda row: get_nested_item(row, schema
                                                                          ['properties'],
                                                                          row.parents +
                                                                          (row.field, )),
                                              axis=1)
    return df_fields


def get_flatland_field(jsonschema_field):
    kwargs = {'optional': True}
    for k in ('default', ):
        if k in jsonschema_field.attributes:
            kwargs[k] = jsonschema_field.attributes[k]

    JSONSCHEMA_TO_FLATLAND_TYPES = {
        'boolean': Boolean,
        'integer': Integer,
        'number': Float,
        'string': String,
    }

    if 'enum' in jsonschema_field.attributes:
        # JSON schema field has enumerated values.  `Enum` is a special
        # type in Flatland.
        flatland_type = Enum
    else:
        flatland_type = JSONSCHEMA_TO_FLATLAND_TYPES[jsonschema_field
                                                     .field_type]
    if flatland_type == String:
        # Do not strip string.
        kwargs['strip'] = False
    kwargs['validators'] = []
    if 'minimum' in jsonschema_field.attributes:
        kwargs['validators'] += [ValueAtLeast(jsonschema_field
                                              .attributes['minimum'])]
    if 'maximum' in jsonschema_field.attributes:
        kwargs['validators'] += [ValueAtMost(jsonschema_field
                                             .attributes['maximum'])]
    flatland_field = flatland_type.using(**kwargs)
    if 'enum' in jsonschema_field.attributes:
        flatland_field = flatland_field.valued(*jsonschema_field.attributes
                                               ['enum'])
    return flatland_field


def get_nested_item(row, d, keys):
    d_i = d
    for k_i in keys:
        if d_i.get('type') == 'object' and 'properties' in d_i:
            d_i = d_i['properties']
        d_i = d_i[k_i]
    return d_i


def get_types(root, func, parents=None):
    if parents is None:
        parents = []

    result = {}
    for i, (k, v) in enumerate(root.iteritems()):
        parents_i = parents + [k]
        if isinstance(v, dict) and v.get('type') == 'object':
            result[k] = get_types(v['properties'], func, parents=parents_i)
        else:
            try:
                result[k] = func(v.get('index', len(root) + i),
                                 k, v, parents_i)
            except Skip:
                pass
    return result


class SchemaDialog(FormViewDialog):
    default_parent = None

    def __init__(self, schema, **kwargs):
        self.validator = jsonschema.Draft4Validator(schema)
        self.df_fields = get_fields_frame(schema)
        form_class = fields_frame_to_flatland_form_class(self.df_fields)
        super(SchemaDialog, self).__init__(form_class, **kwargs)

    def create_ui(self):
        super(SchemaDialog, self).create_ui()
        self.label_error = gtk.Label()
        self.label_event_box = gtk.EventBox()
        self.label_event_box.add(self.label_error)
        self.vbox_errors = gtk.VBox()
        self.vbox_errors.add(self.label_event_box)
        self.vbox_form.add(self.vbox_errors)
        self.vbox_errors.show_all()
        self.vbox_errors.hide()
        buttons_by_label = dict([(c.props.label, c)
                                 for c in self.window.action_area.children()])
        self.button_ok = buttons_by_label['gtk-ok']

    def on_changed(self, form_view, proxy_group, proxy, field_name, new_value):
        self.validate()

    def validate(self):
        data_dict = expand_items(flatten_form(self.form_view.form.schema)
                                 .items())
        errors = OrderedDict([('.'.join(e.path), e)
                              for e in self.validator.iter_errors(data_dict)])

        # Light red color.
        light_red = gtk.gdk.Color(240 / 255., 126 / 255., 110 / 255.)

        for name_i, field_i in self.form_view.form.fields.iteritems():
            color_i = light_red if name_i in errors else None
            label_widget_i = (field_i.widget
                              .get_data('pygtkhelpers::label_widget'))
            label_widget_i.get_parent().modify_bg(gtk.STATE_NORMAL, color_i)

        if errors:
            self.button_ok.set_sensitive(False)
            message = '\n'.join(['[{}] {}'.format(name, error.message)
                                 for name, error in errors.iteritems()])
            self.label_event_box.modify_bg(gtk.STATE_NORMAL, light_red)
            self.label_error.set_markup(message)
            self.vbox_errors.show()
        else:
            self.button_ok.set_sensitive(True)
            self.label_error.set_markup('')
            self.vbox_errors.hide()

    def create_form_view(self, values=None, use_markup=True):
        self.form_view = create_form_view(self.form_class, values=values,
                                          use_markup=use_markup)
        self.validate()


class MetaDataDialog(SchemaDialog):
    def __init__(self, schema, pipeline_command=None, **kwargs):
        from barcode_scanner.scanner import BarcodeScanner

        super(MetaDataDialog, self).__init__(schema, **kwargs)
        self.scanner = BarcodeScanner(pipeline_command)

    def create_ui(self):
        from barcode_scanner.gtk_matplotlib import ScannerView

        super(MetaDataDialog, self).create_ui()
        self.scanner_view = ScannerView(self.scanner)
        self.scanner_view.widget.show_all()

        self.scanner_window = gtk.Dialog(title='Barcode scan',
                                         parent=self.window,
                                         flags=gtk.DIALOG_MODAL |
                                         gtk.DIALOG_DESTROY_WITH_PARENT)
        (self.scanner_window.get_content_area()
         .pack_start(self.scanner_view.widget))
        self.scanner.start()

    def create_form_view(self, values=None, use_markup=True):
        super(MetaDataDialog, self).create_form_view(values, use_markup)
        table = self.form_view.widget.get_children()[0]
        children = table.get_children()

        def on_symbols_found_i(scanner, np_img, symbols, row_i):
            from .proxy import proxy_for

            # Stop listening for `symbols-found` signal.
            scanner.disconnect(row_i['callback_ids']['symbol'])
            del row_i['callback_ids']['symbol']

            # Concatenate symbols text as comma-separated list.
            symbol_data = ', '.join([symbol_j['data'] for symbol_j in symbols])

            # Fill widget with scanned value (if possible).
            proxy = proxy_for(row_i['widget'])
            try:
                proxy.set_widget_value(symbol_data)
            except TypeError:
                logger.error('Could not set value for "%s"',
                             row_i['label'].get_label(), exc_info=True)
            else:
                # Make system bell sound to indicate a scan has
                # completed.
                print '\a\a',

            # Re-enable the scan button.
            row_i['button'].set_sensitive(True)

            # Close scan dialog after a short delay (let user see the
            # scanned match).
            gtk.timeout_add(1000, lambda *args:
                            self.scanner_window.hide())
            return True

        # Attach callback for when scan dialog is closed.
        def on_scanner_view__delete_event(window, event, row_i):
            '''
            When scanner view is closed, stop the scan, hide the window and
            re-enable the button that initiated the scan.
            '''
            # Disable scanner to reduce CPU usage and prevent unexpected
            # `symbols-found` signals.  Note that GStreamer video pipeline
            # stays running.
            self.scanner_view.disable_scan()
            # Hide scanner dialog window.
            self.scanner_window.hide()
            # Enable scan button.
            row_i['button'].set_sensitive(True)
            self.scanner_window.disconnect(row_i['callback_ids']
                                           ['scanner_window'])
            del row_i['callback_ids']['scanner_window']
            return gtk.TRUE

        # From list of `gtk.Table` widget children, extract list of `(widget,
        # event_box)` pairs, one pair per form field.
        # N.B., table widgets are listed in reverse order of insertion in list
        # of children, so list of pairs is reversed (i.e., `[::-1]`).
        widget_pairs = [children[2 * i:2 * i + 2]
                        for i in xrange(len(self.form_view.form.schema))][::-1]

        for i, (name_i, form_field_i) in enumerate(self.form_view.form.schema
                                                   .iteritems()):
            widget_i, event_box_i = widget_pairs[i]
            label_i = event_box_i.get_children()[0]

            # Add scan button beside each widget.
            button_scan_i = gtk.Button('Scan')
            button_scan_i.show()
            table.attach(button_scan_i, 2, 3, i, i + 1)
            button_scan_i.props.name = label_i.get_label()

            # Add callback function for each scan button to launch a barcode
            # scanning dialog.
            def on_button_scan_i__clicked(i, widget, event_box, label):
                # Wrap callback to bind widget, etc. data to callback.  This is
                # necessary, since the `widget_i, label_i, etc.`, references
                # are modified during each loop iteration.
                def wrapped(button):
                    # Disable button until scan has completed or is cancelled.
                    button.set_sensitive(False)

                    row_i = {'widget': widget,
                             'event_box': event_box,
                             'label': label,
                             'label_label': label.get_label(),
                             'button': button,
                             'callback_ids': {}}

                    # Attach callback to signal triggered when symbol/symbols are
                    # found by the scanner.
                    row_i['callback_ids']['symbol'] =\
                        self.scanner.connect('symbols-found',
                                             on_symbols_found_i, row_i)
                    row_i['callback_ids']['scanner_window'] =\
                        self.scanner_window.connect('delete_event',
                                                    on_scanner_view__delete_event,
                                                    row_i)

                    # Launch barcode scan dialog.
                    self.scanner_window.show()
                    self.scanner_view.enable_scan()
                return wrapped

            button_scan_i.connect('clicked',
                                  on_button_scan_i__clicked(i, widget_i,
                                                            event_box_i,
                                                            label_i))

    def run(self, values=None, parent=None, use_markup=True):
        # Run dialog.
        result = super(MetaDataDialog, self).run(values=values, parent=parent,
                                                 use_markup=use_markup)
        try:
            # Destroy scan widget.
            self.scanner_view.hide()

            # Stop scanner.
            self.scanner.stop()
        finally:
            return result


def schema_dialog(schema, data=None, device_name=None, max_width=None,
                  max_fps=None, title=None, parent=None):
    '''
    Args
    ----

        schema (dict) : jsonschema definition.  Each property *must* have a
            default value.
        device_name (str or list-like) : GStreamer video source device name.
        max_width (int) : Maximum video frame width.
        max_fps (float) : Maximum video frame rate (frames/second).

    Returns
    -------

        (dict) : json-encodable dictionary containing validated values for
            properties included in the specified schema.

    Raises `KeyError` if no video configuration is found that matches the
    specified parameters, and `ValueError` if values to not validate.
    '''
    with nostderr():
        import pygst_utils as pu

    gtk.threads_init()
    df_modes = pu.get_available_video_source_configs()
    query = (df_modes.width == df_modes.width)
    if device_name is not None:
        if isinstance(device_name, types.StringTypes):
            query &= (df_modes.device_name == device_name)
        else:
            query &= (df_modes.device_name.isin(device_name))
    if max_width is not None:
        query &= (df_modes.width <= max_width)
    if max_fps is not None:
        query &= (df_modes.framerate <= max_fps)
    df_modes = df_modes.loc[query]
    if not df_modes.shape[0]:
        raise KeyError('No compatible video mode found.')
    config = df_modes.sort_values(['width', 'framerate'],
                                  ascending=False).iloc[0]
    pipeline_command = pu.pipeline_command_from_json(config, colorspace='rgb')
    dialog = MetaDataDialog(schema, pipeline_command, title=title,
                            parent=parent)
    with nostderr():
        valid, results = dialog.run(values=data)
    if not valid:
        raise ValueError('Invalid values.')
    return results
