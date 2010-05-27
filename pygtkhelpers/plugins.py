# -*- coding: utf-8 -*-

"""
    pygtkhelpers.plugins
    ~~~~~~~~~~~~~~~~~~~~

    Extending GTK WIdgets (or any GObject) without subclassing them.

    :copyright: 2010 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)

"""

from pygtkhelpers.utils import GObjectUserDataProxy


def apply_plugins(widget, *plugin_types, **named_plugin_types):
    """Apply some plugins to a widget.

    :param widget: The widget to apply plugins to.
    :param plugin_types: A list of plugin types, which will be instantiated
                         and applied to the widget with the default name of
                         the plugin.
    :param named_plugin_types: A named list of plugins, the keywords will be
                               the name of the plugin when loaded and will
                               override the default plugin name. This can
                               allow loading the same plugin multpily for the
                               same widget under different names.

    Plugins should conform to the GObjectPlugin interface or be a subclass of
    it. Once loaded, plugins will be available as widget.plugins.<plugin_name>
    withe standard attribute access.
    """
    if not hasattr(widget, 'plugins'):
        widget.plugins = GObjectUserDataProxy(widget)
    for plugin_type in plugin_types:
        plugin = plugin_type(widget)
        setattr(widget.plugins, plugin.plugin_name, plugin)
    for name, plugin_type in named_plugin_types.items():
        plugin = plugin_type(widget, plugin_name=name)
        setattr(widget.plugins, plugin.plugin_name, plugin)


class GObjectPlugin(object):
    """A base class for plugins for GObjects

    :param widget: The widget to apply the plugin to
    :param plugin_name: Optional name to override the class `plugin_name`
                        attribute to load a plugin under a non-default name.

    .. note::

        Either the class's plugin_name should be set or plugin_name must be
        passed to the constructor, otherwise `ValueError` will be raised.
    """

    #: The default plugin name for instances of this plugin
    plugin_name = None

    def __init__(self, widget, plugin_name=None):
        self.widget = widget
        self.plugin_name = plugin_name or self.plugin_name
        if self.plugin_name is None:
            raise ValueError('plugin_name must be set.')
        self.create_ui()

    def create_ui(self):
        """Create the user interface

        For overriding in implementations.
        """

