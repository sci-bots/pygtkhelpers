

import os
import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import run_in_window, gsignal

from person import Person, date


class PersonForm(SlaveView):

    builder_path = os.path.join(os.path.dirname(__file__), 'address_form.ui')
    
    def create_ui(self):
        self.connect('model-set', self._on_set_model)
        def print_model(slave):
            print slave.model
        self.connect('model-updated', print_model)

    def _on_set_model(self, _):
        if self.model:
            self.firstname_entry.props.text = self.model.name
            self.lastname_entry.props.text = self.model.surname
            self.email_entry.props.text = self.model.email
        else:
            self.firstname_entry.props.text = ""
            self.lastname_entry.props.text = ""
            self.email_entry.props.text = ""

    def on_firstname_entry__changed(self, entry):
        if self.model:
            self.model.name = entry.props.text
            self.emit('model-updated')

    def on_lastname_entry__changed(self, entry):
        if self.model:
            self.model.surname = entry.props.text
            self.emit('model-updated')

    def on_email_entry__changed(self, entry):
        if self.model:
            self.model.email = entry.props.text
            self.emit('model-updated')


if __name__=='__ main__':
    person = Person('hans', 'man', 'hans.man@example.com')
    view = PersonForm()
    view.set_model(person)
    run_in_window(view)
