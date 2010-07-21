# -*- coding: utf-8 -*-

"""
    pygtkhelpers.addons
    ~~~~~~~~~~~~~~~~~~~~

    Extending GTK WIdgets (or any GObject) without subclassing them.

    :copyright: 2010 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)

"""

from pygtkhelpers.utils import GObjectUserDataProxy


def apply_addons(widget, *addon_types, **named_addon_types):
    """Apply some addons to a widget.

    :param widget: The widget to apply addons to.
    :param addon_types: A list of addon types, which will be instantiated
                         and applied to the widget with the default name of
                         the addon.
    :param named_addon_types: A named list of addons, the keywords will be
                               the name of the addon when loaded and will
                               override the default addon name. This can
                               allow loading the same addon multpily for the
                               same widget under different names.

    Plugins should conform to the GObjectPlugin interface or be a subclass of
    it. Once loaded, addons will be available as widget.addons.<addon_name>
    withe standard attribute access.
    """
    for addon_type in addon_types:
        addon_type(widget)

    for name, addon_type in named_addon_types.items():
        addon_type(widget, addon_name=name)


def apply_addon(widget, addon_type, **kw):
    """Apply a single addon to a widget

    :param widget: The widget to apply the addon to.
    :param kw: A dict of keyword arguments to be passed to the addon
    """
    return addon_type(widget, **kw)


class GObjectPlugin(object):
    """A base class for addons for GObjects

    :param widget: The widget to apply the addon to
    :param addon_name: Optional name to override the class `addon_name`
                        attribute to load a addon under a non-default name.

    .. note::

        Either the class's addon_name should be set or addon_name must be
        passed to the constructor, otherwise `ValueError` will be raised.
    """

    #: The default addon name for instances of this addon
    addon_name = None

    def __init__(self, widget, addon_name=None, **kw):
        self.widget = widget
        self.addon_name = addon_name or self.addon_name
        if self.addon_name is None:
            raise ValueError('addon_name must be set.')
        if not hasattr(widget, 'addons'):
            widget.addons = GObjectUserDataProxy(widget)
        setattr(widget.addons, self.addon_name, self)
        self.configure(**kw)

    def configure(self, **kw):
        """Configure and initialise the addon

        For overriding in implementations.
        """

