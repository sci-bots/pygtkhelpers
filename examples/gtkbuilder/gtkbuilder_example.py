#!/usr/bin/python

import sys, os

import gtk, gobject

from pygtkhelpers.delegates import SlaveView, WindowView
from pygtkhelpers.utils import run_in_window, gsignal


class MenuView(SlaveView):
    builder_path = os.path.join(os.path.dirname(__file__), 'interface.ui')
    toplevel_name = 'menubar1'

class ToolbarView(SlaveView):

    gsignal('new-button-clicked')

    builder_path = os.path.join(os.path.dirname(__file__), 'interface.ui')
    toplevel_name = 'toolbar1'
    def create_ui(self):
        self.widget.insert(gtk.ToolButton(gtk.STOCK_SAVE),0)
        self.widget.insert(gtk.ToolButton(gtk.STOCK_OPEN),0)

        self.new_button = gtk.ToolButton(gtk.STOCK_NEW)
        self.widget.insert(self.new_button,0)
    def on_new_button__clicked(self, *a):
        self.emit('new-button-clicked')

class UserListView(SlaveView):
    builder_path = os.path.join(os.path.dirname(__file__), 'interface.ui')
    toplevel_name = 'scrolledwindow1'

class UserView(SlaveView):
    builder_path = os.path.join(os.path.dirname(__file__), 'interface.ui')
    toplevel_name = 'table1'

class UserBrowser(SlaveView):
    def create_ui(self):
        hbox = gtk.HBox()
        self.widget.add(hbox)

        self.user_list_view = UserListView()
        self.user_view = UserView()
        hbox.add(self.user_list_view.widget)
        hbox.add(self.user_view.widget)

class StatusView(SlaveView):
    builder_path = os.path.join(os.path.dirname(__file__), 'interface.ui')
    toplevel_name = 'statusbar1'

class MainWindowView(WindowView):
    def create_ui(self):
        vbox = gtk.VBox()
        self.widget.add(vbox)
        
        #the gtkBuilder file specifies expand=False, but that is a packing 
        #option that gets ignored when we create a slave view; we must specify 
        #it manually when we pack.
        vbox.pack_start(MenuView().widget, expand=False)     
        
        self.toolbar_view = ToolbarView()
        vbox.pack_start(self.toolbar_view.widget, expand=False)

        self.user_browser = UserBrowser()
        vbox.add(self.user_browser.widget)
        vbox.pack_end(StatusView().widget, expand=False)
    
    def on_toolbar_view__new_button_clicked(self, *a):
        print 'New user ', self.user_browser.user_view.entry1.get_text(), '.'

if __name__ == '__main__':
    view = MainWindowView()
    run_in_window(view)
