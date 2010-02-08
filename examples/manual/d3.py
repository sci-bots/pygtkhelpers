
"""Reusable Components, Delegate Example 3
"""
import gtk
from pygtkhelpers.delegates import WindowView, SlaveView

class UserView(SlaveView):
    """A view for a single user"""
    def create_ui(self):
        self.entry = gtk.Entry()
        self.widget.add(self.entry)

class ApplicationView(WindowView):
    """The main interface for my user management program"""
    def create_ui(self):
        # This time, create a slave view, and add it to the
        self.user_slave = self.add_slave(UserView(), 'widget')

if __name__ == '__main__':
    ApplicationView().show_and_run()

