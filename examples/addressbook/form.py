

import os
import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import run_in_window, gsignal

from person import Person, date


class PersonView(SlaveView):

    builder_path = os.path.join(os.path.dirname(__file__), 'address_form.ui')
    
    def create_ui(self):
        self.connect('model-set', self._on_set_model)
        def print_model(slave):
            print slave.model
        self.connect('model-updated', print_model)

    def _on_set_model(self, _):
        self.firstname_entry.props.text = self.model.name
        self.lastname_entry.props.text = self.model.surname
        self.email_entry.props.text = self.model.email

    def on_firstname_entry__changed(self, entry):
        self.model.name = entry.props.text
        self.emit('model-updated')

    def on_lastname_entry__changed(self, entry):
        self.model.surname = entry.props.text
        self.emit('model-updated')

    def on_email_entry__changed(self, entry):
        self.model.email = entry.props.text
        self.emit('model-updated')


if __name__=='__main__':
    person = Person('hans', 'man', 'hans.man@example.com')
    view = PersonView()
    view.set_model(person)
    run_in_window(view)
