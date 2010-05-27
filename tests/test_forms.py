

from pygtkhelpers.utils import refresh_gui
from pygtkhelpers.test import CheckCalled



import gtk

from pygtkhelpers.forms import FormView, Field

from flatland import Dict, String, Integer, Boolean


class PersonForm(FormView):

    schema_type = Dict.of(
        String.named('name'),
        Integer.named('age'),
        Boolean.named('friendly'),
    )

def test_form_fields():
    f = PersonForm()
    assert isinstance(f.name, gtk.Entry)
    assert isinstance(f.age, gtk.SpinButton)
    assert isinstance(f.friendly, gtk.CheckButton)


def test_form_field_value_changed():
    f = PersonForm()
    check = CheckCalled(f.form.proxies, 'changed')
    f.name.set_text('hello')
    assert check.called[2] == 'name'
    assert check.called[3] == 'hello'


def test_update_schema_value():
    f = PersonForm()
    assert f.form.schema['name'].value == None
    f.name.set_text('hello')
    assert f.form.schema['name'].value == 'hello'


def test_update_schema_value_typed():
    f = PersonForm()
    assert f.form.schema['friendly'].value == None
    f.friendly.set_active(True)
    assert f.form.schema['friendly'].value == True
    f.friendly.set_active(False)
    assert f.form.schema['friendly'].value == False


