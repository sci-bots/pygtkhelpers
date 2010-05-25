
from flatland import Form, Dict, String, Integer, Boolean
from flatland.validation import ValueAtLeast, ValueAtMost

from pygtkhelpers.forms import FormView


class PersonSchema(Form):

    name = String

    age = Integer.using(validators=[
        ValueAtLeast(minimum=18),
        ValueAtMost(maximum=120)
    ])

    weight = Integer.using(validators=[
        ValueAtLeast(minimum=0),
        ValueAtMost(maximum=300)
    ])
    weight.render_options = dict(
        style='slider'
    )

    friendly = Boolean

    address = String.using()
    address.render_options = dict(
        style='multiline'
    )

    happy = Boolean.using()
    happy.render_options = dict(
        style='toggle'
    )


class PersonView(FormView):

    schema_type = PersonSchema

if __name__ == '__main__':
    PersonView().show_and_run()

