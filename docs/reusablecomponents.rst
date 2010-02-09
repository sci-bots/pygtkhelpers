
Building Reusable User Interface Components
===========================================

This chapter will describe how reusable components can be created using
pygtkhelpers delegate system. A delegate is a controller for a GTK view. It
interacts closely with GTK, managing such things as signal handling.

Before we start, it is worth considering the alternative method of
creating reusable components, which is custom widgets. This is not a scalable
solution, in that writing custom widgets can only be performed using pure
PyGTK, rather than GtkBuilder files. The maintainance requirement of coded
views versus ui-designed views is large, and using custom widgets in this way
would not allow component hierarchies of ui-designed interfaces.


Your first view
~~~~~~~~~~~~~~~

So, what we will first need is a GTK view. This is what we want to display and
take control of in our delegate. This view can be created using a UI Builder
like Glade, or it can be coded by hand in XML, or in Python, or a combination
of these. The delegate doesn't care *how* you make your GTK, and in fact, from
experience, we know that you will likely mix and match in the same view.

The first thing you will need to do is subclass the View type. This should be
performed for every individual view that is required to be a reusable
component. The type of View you subclass depends on whether the view is a
top-level widget (Window, Dialog, ...) or a slave widget, which can be placed
inside other widgets. The available delegate types are
:class:`~pygtkhelpers.delegates.SlaveView` and
`~pygtkhelpers.delegates.WindowView`:

.. literalinclude:: ../examples/manual/d1.py

I just shows a toplevel Window, with no widgets inside. We are going to leave
that like that, and create a component to go inside. Remember *reusable
components*, there is no point putting UI straight into the Window, although
you could do that, and pygtkhelpers won't stop you:

.. literalinclude:: ../examples/manual/d2.py

This just adds an entry to the widget, which you can see as you run it.


Combining multiple views
~~~~~~~~~~~~~~~~~~~~~~~~

As mentioned, it is best to separte components by their use, so for example in
our user mangement application, the view to edit a User, might be consistent
throughout the application. You may want it next to a list, or you may want it
in a dialog. Either way, this should be separated out into it's own view.

This time, we will be using a SlaveView instance, which will be added to our
main view. Adding slaves is achieved with the
:meth:`~pygtkhelpers.delegates.SlaveView.add_slave` method, and is shown in
the following example:

.. literalinclude:: ../examples/manual/d3.py

