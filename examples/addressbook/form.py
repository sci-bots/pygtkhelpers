

import os
import gtk
from pygtkhelpers.delegates import SlaveView
from pygtkhelpers.utils import run_in_window, gsignal

from person import Person


class PersonForm(SlaveView):

    builder_path = os.path.join(os.path.dirname(__file__), 'address_form.ui')
    
    def create_ui(self):
        self.reset()
        def print_model(slave):
            print slave.model
        self.connect('model-updated', print_model)

    def reset(self):
        self.firstname_entry.set_text('')
        self.lastname_entry.set_text('')
        self.email_entry.set_text('')

    def on_model_set(self):
        if self.model:
            self.firstname_entry.set_text(self.model.name)
            self.lastname_entry.set_text(self.model.surname)
            self.email_entry.set_text(self.model.email)
        else:
            self.reset()

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


if __name__=='__main__':
    person = Person('hans', 'man', 'hans.man@example.com')
    view = PersonForm()
    view.set_model(person)
    run_in_window(view)
