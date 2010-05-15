
"""Reusable Components, Delegate Example 7
"""
import gtk
from pygtkhelpers.utils import gsignal
from pygtkhelpers.delegates import WindowView, SlaveView


class LoginView(SlaveView):

    gsignal('entry-changed')

    def create_ui(self):
        self.entry = gtk.Entry()
        self.widget.add(self.entry)

    def on_entry__changed(self, entry):
        self.emit('entry-changed')


class ApplicationView(WindowView):
    """The main interface for my user management program"""

    def create_ui(self):
        self.login_slave = self.add_slave(LoginView(), 'widget')

    def on_login_slave__entry_changed(self, slave):
        print 'entry was changed'

if __name__ == '__main__':
    ApplicationView().show_and_run()

