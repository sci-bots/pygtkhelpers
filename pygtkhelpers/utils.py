# -*- coding: utf-8 -*-

"""
    pygtkhelpers.utils
    ~~~~~~~~~~~~~~~~~~

    Utilities for handling some of the wonders of PyGTK.

    gproperty and gsignal are mostly taken from kiwi.utils

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

import sys, struct, time, string

import gobject, gtk

from cgi import escape as _xml_escape


def gsignal(name, *args, **kwargs):
    """Add a GObject signal to the current object.

    It current supports the following types:
        - str, int, float, long, object, enum

    :param name: name of the signal
    :param args: types for signal parameters,
        if the first one is a string 'override', the signal will be
        overridden and must therefor exists in the parent GObject.

    .. note:: flags: A combination of;

      - gobject.SIGNAL_RUN_FIRST
      - gobject.SIGNAL_RUN_LAST
      - gobject.SIGNAL_RUN_CLEANUP
      - gobject.SIGNAL_NO_RECURSE
      - gobject.SIGNAL_DETAILED
      - gobject.SIGNAL_ACTION
      - gobject.SIGNAL_NO_HOOKS

    """

    frame = sys._getframe(1)
    try:
        locals = frame.f_locals
    finally:
        del frame

    dict = locals.setdefault('__gsignals__', {})

    if args and args[0] == 'override':
        dict[name] = 'override'
    else:
        retval = kwargs.get('retval', None)
        if retval is None:
            default_flags = gobject.SIGNAL_RUN_FIRST
        else:
            default_flags = gobject.SIGNAL_RUN_LAST

        flags = kwargs.get('flags', default_flags)
        if retval is not None and flags != gobject.SIGNAL_RUN_LAST:
            raise TypeError(
                "You cannot use a return value without setting flags to "
                "gobject.SIGNAL_RUN_LAST")

        dict[name] = (flags, retval, args)

def _max(c):
    # Python 2.3 does not like bitshifting here
    return 2 ** ((8 * struct.calcsize(c)) - 1) - 1

_MAX_VALUES = {int : _max('i'),
               float: float(2**1024 - 2**971),
               long : _max('l') }
_DEFAULT_VALUES = {str : '', float : 0.0, int : 0, long : 0L}


def gproperty(name, ptype, default=None, nick='', blurb='',
              flags=gobject.PARAM_READWRITE, **kwargs):
    """Add a GObject property to the current object.

    :param name:   name of property
    :param ptype:   type of property
    :param default:  default value
    :param nick:     short description
    :param blurb:    long description
    :param flags:    parameter flags, a combination of:
      - PARAM_READABLE
      - PARAM_READWRITE
      - PARAM_WRITABLE
      - PARAM_CONSTRUCT
      - PARAM_CONSTRUCT_ONLY
      - PARAM_LAX_VALIDATION

    Optional, only for int, float, long types:

    :param minimum: minimum allowed value
    :param: maximum: maximum allowed value
    """

    # General type checking
    if default is None:
        default = _DEFAULT_VALUES.get(ptype)
    elif not isinstance(default, ptype):
        raise TypeError("default must be of type %s, not %r" % (
            ptype, default))
    if not isinstance(nick, str):
        raise TypeError('nick for property %s must be a string, not %r' % (
            name, nick))
    nick = nick or name
    if not isinstance(blurb, str):
        raise TypeError('blurb for property %s must be a string, not %r' % (
            name, blurb))

    # Specific type checking
    if ptype == int or ptype == float or ptype == long:
        default = (kwargs.get('minimum', ptype(0)),
                   kwargs.get('maximum', _MAX_VALUES[ptype]),
                   default)
    elif ptype == bool:
        if (default is not True and
            default is not False):
            raise TypeError("default must be True or False, not %r" % (
                default))
        default = default,
    elif gobject.type_is_a(ptype, gobject.GEnum):
        if default is None:
            raise TypeError("enum properties needs a default value")
        elif not isinstance(default, ptype):

            raise TypeError("enum value %s must be an instance of %r" %
                            (default, ptype))
        default = default,
    elif ptype == str:
        default = default,
    elif ptype == object:
        if default is not None:
            raise TypeError("object types does not have default values")
        default = ()
    else:
        raise NotImplementedError("type %r" % ptype)

    if flags < 0 or flags > 32:
        raise TypeError("invalid flag value: %r" % (flags,))

    frame = sys._getframe(1)
    try:
        locals = frame.f_locals
        dict = locals.setdefault('__gproperties__', {})
    finally:
        del frame

    dict[name] = (ptype, nick, blurb) + default + (flags,)


def refresh_gui(delay=0.0001, wait=0.0001):
    """Use up all the events waiting to be run

    :param delay: Time to wait before using events
    :param wait: Time to wait between iterations of events

    This function will block until all pending events are emitted. This is
    useful in testing to ensure signals and other asynchronous functionality
    is required to take place.
    """
    time.sleep(delay)
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
        time.sleep(wait)



def _get_in_window(widget):
    from .delegates import BaseDelegate
    if isinstance(widget, gtk.Window):
        return widget
    elif isinstance(widget, BaseDelegate):
        return _get_in_window(widget.widget)
    else:
        w = gtk.Window()
        w.add(widget)
        return w


def run_in_window(target, on_destroy=gtk.main_quit):
    """Run a widget, or a delegate in a Window
    """
    w = _get_in_window(target)
    if on_destroy:
        w.connect('destroy', on_destroy)
    w.resize(500, 400)
    w.move(100, 100)
    w.show_all()
    gtk.main()


class GObjectUserDataProxy(object):
    """Proxy the GObject data interface to attribute-based access

    :param widget: The widget for which to provide attribute access

    >>> import gtk
    >>> from pygtkhelpers.utils import GObjectUserDataProxy
    >>> w = gtk.Label()
    >>> data = GObjectUserDataProxy(w)
    >>> data.foo = 123
    >>> data.foo
    123
    >>> w.get_data('foo')
    123
    >>> w.set_data('goo', 456)
    >>> data.goo
    456
    """

    def __init__(self, widget):
        object.__setattr__(self, '_widget', widget)

    def __getattr__(self, attr):
        return self._widget.get_data(attr)

    def __setattr__(self, attr, value):
        self._widget.set_data(attr, value)

    def __delattr__(self, attr):
        self._widget.set_data(attr, None)


class XFormatter(string.Formatter):
    """
    extended string formatter supporting xml entity escape
    """
    def __init__(self, *lookup_objects, **extra_converters):
        # add e as xml escape converter if the name is not used
        if 'e' not in extra_converters:
            extra_converters['e'] = _xml_escape
        self.extra_converters = extra_converters
        self.lookup_objects = lookup_objects


    def get_value(self, key, args, kwargs):
        try:
            return super(XFormatter, self).get_value(key, args, kwargs)
        except LookupError:
            if isinstance(key, basestring):
                for obj in self.lookup_objects:
                    if hasattr(obj, key):
                        return getattr(obj, key)
            raise # reraise the lookup error

    def convert_field(self, value, conversion):
        if conversion in self.extra_converters:
            return self.extra_converters[conversion](value)
        return super(XFormatter, self).convert_field(value, conversion)

    def format_field(self, value, conversion):
        if conversion in self.extra_converters:
            return self.extra_converters[conversion](value)
        return super(XFormatter, self).format_field(value, conversion)


def eformat(format, *k, **kw):
    return XFormatter().vformat(format, k, kw)

class MarkupMixin(object):
    """
    adds a markup property based on eformat
    using self.format as format string
    and self=self as format args
    """
    format = None

    markup_converters = {}

    def markup_kwargs(self):
        return {}

    @property
    def markup(self):
        formatter = XFormatter(self, **self.markup_converters)
        return formatter.vformat(self.format, (), self.markup_kwargs())
