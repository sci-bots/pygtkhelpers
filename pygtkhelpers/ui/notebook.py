import sys
import os
import collections

import gtk
from path_helpers import path
try:
    from ipython_helpers.notebook import SessionManager
except ImportError:
    print >> sys.stderr, ('The NotebookManagerView requires the '
                          '`ipython-helpers` package.')
    raise
from ..delegates import SlaveView
from .dialogs import yesno


class NotebookManagerView(SlaveView):
    def __init__(self, notebook_dir=None, template_dir=None):
        super(NotebookManagerView, self).__init__()
        if notebook_dir is None:
            notebook_dir = os.getcwd()
        self.notebook_dir = path(notebook_dir).abspath()
        self.template_dir = template_dir
        self.notebook_manager = SessionManager(daemon=True)

    def create_ui(self):
        box = gtk.HBox()

        new_button = gtk.Button('New...')
        open_button = gtk.Button('Open...')
        new_button.connect('clicked', self.on_new)
        open_button.connect('clicked', self.on_open)
        new_button.show()
        open_button.show()

        box.pack_end(new_button, False, False, 0)
        box.pack_end(open_button, False, False, 0)
        self.widget.pack_start(box, False, False, 0)

        self.parent = None
        parent = self.widget.get_parent()
        while parent is not None:
            self.parent = parent
            parent = parent.get_parent()

    def on_open(self, button):
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                   gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        dialog = gtk.FileChooserDialog("Open notebook", self.parent,
                                       gtk.FILE_CHOOSER_ACTION_OPEN, buttons)
        add_filters(dialog, [{'name': 'IPython notebook (*.ipynb)',
                              'pattern': '*.ipynb'}])
        dialog.set_current_folder(self.notebook_dir)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            selected_path = dialog.get_filename()
            self.notebook_manager.open(selected_path)
        dialog.destroy()

    def on_new(self, button):
        '''
        Copy selected notebook template to notebook directory.

        ## Notes ##

         - An exception is raised if the parent of the selected file is the
           notebook directory.
         - If notebook with same name already exists in notebook directory,
           offer is made to overwrite (the new copy of the file is renamed with
           a count if overwrite is not selected).
        '''
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                   gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        dialog = gtk.FileChooserDialog("Select notebook template", self.parent,
                                       gtk.FILE_CHOOSER_ACTION_OPEN, buttons)
        add_filters(dialog, [{'name': 'IPython notebook (*.ipynb)',
                              'pattern': '*.ipynb'}])
        if self.template_dir is not None:
            dialog.set_current_folder(self.template_dir)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            selected_path = path(dialog.get_filename())
            output_path = self.notebook_dir.joinpath(selected_path.name)

            overwrite = False
            if output_path.isfile():
                response = yesno('%s already exists. Overwrite?' % output_path.name)
                if response == gtk.RESPONSE_YES:
                    overwrite = True
                else:
                    counter = 1
                    renamed_path = output_path
                    while renamed_path.isfile():
                        new_name = '%s (%d)%s' % (output_path.namebase, counter,
                                                  output_path.ext)
                        renamed_path = output_path.parent.joinpath(new_name)
                        counter += 1
                    output_path = renamed_path
            self.notebook_manager.launch_from_template(selected_path,
                                                       overwrite=overwrite,
                                                       output_name=output_path.name,
                                                       notebook_dir=self.notebook_dir)
        dialog.destroy()

    def stop(self):
        self.notebook_manager.stop()

    def __del__(self):
        self.stop()


def add_filters(dialog, filters):
    for f in filters:
        filter_text = gtk.FileFilter()
        filter_text.set_name(f['name'])
        if 'mime_type' in f:
            mime_types = f['mime_type']
            if not isinstance(mime_types, collections.Iterable):
                mime_types = [mime_types]
            for mime_type in mime_types:
                filter_text.add_mime_type(mime_type)
        elif 'pattern' in f:
            patterns = f['pattern']
            if not isinstance(patterns, collections.Iterable):
                patterns = [patterns]
            for pattern in patterns:
                filter_text.add_pattern(pattern)
        dialog.add_filter(filter_text)
