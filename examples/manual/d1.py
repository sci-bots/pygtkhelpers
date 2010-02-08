
"""Reusable components, Delegate Example 1
"""
import gtk
from pygtkhelpers.delegates import WindowView

class UserView(WindowView):
    """The user interface for my user management ogram"""

if __name__ == '__main__':
    UserView().show_and_run()

