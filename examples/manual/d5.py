
"""Reusable Components, Delegate Example 5
"""
import gtk
from pygtkhelpers.delegates import WindowView

class ApplicationView(WindowView):
    """The main interface for my user management program"""
    def create_ui(self):
        self.entry = gtk.Entry()
        self.widget.add(self.entry)

    def on_entry__changed(self, entry):
        print entry.get_text()

    def on_widget__delete_event(self, window, event):
        self.hide_and_quit()

if __name__ == '__main__':
    ApplicationView().show_and_run()

