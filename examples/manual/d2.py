
"""Reusable Components, Delegate Example 2
"""
import gtk
from pygtkhelpers.delegates import WindowView

class UserView(WindowView):
    """The user interface for my user management ogram"""
    def create_ui(self):
        """Create the user interface

           create_ui is a method called during the Delegate's
           initialisation process, to create, add to, or modify any UI
           created by GtkBuilder files.
        """
        self.entry = gtk.Entry()
        self.widget.add(self.entry)

if __name__ == '__main__':
    UserView().show_and_run()

