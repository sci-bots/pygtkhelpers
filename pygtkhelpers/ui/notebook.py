import sys
import os
import collections
import types
import webbrowser

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

    def sessions_dialog(self):
        session_list = NotebookManagerList(self.notebook_manager)
        dialog = gtk.Dialog(title='Notebook session manager',
                            parent=self.parent,
                            flags=gtk.DIALOG_MODAL |
                            gtk.DIALOG_DESTROY_WITH_PARENT,
                            buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK))
        dialog.set_transient_for(self.parent)
        dialog.get_content_area().pack_start(session_list.widget)
        return dialog

    def create_ui(self):
        box = gtk.HBox()

        new_button = gtk.Button('New...')
        open_button = gtk.Button('Open...')
        manager_button = gtk.Button('Manage sessions...')
        new_button.connect('clicked', self.on_new)
        open_button.connect('clicked', self.on_open)
        manager_button.connect('clicked', self.on_manager)

        box.pack_end(new_button, False, False, 0)
        box.pack_end(open_button, False, False, 0)
        box.pack_end(manager_button, False, False, 0)
        self.widget.pack_start(box, False, False, 0)

        self.parent = None
        parent = self.widget.get_parent()
        while parent is not None:
            self.parent = parent
            parent = parent.get_parent()
        self.widget.show_all()

    def get_parent(self):
        self.parent = None
        parent = self.widget.get_parent()
        while parent is not None:
            self.parent = parent
            parent = parent.get_parent()
        return self.parent

    def on_manager(self, button):
        parent = self.get_parent()
        dialog = self.sessions_dialog()
        dialog.show_all()
        if parent is not None:
            parent.set_sensitive(False)
        dialog.run()
        dialog.destroy()
        if parent is not None:
            parent.set_sensitive(True)

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


class NotebookManagerList(SlaveView):
    '''
    Display list of running sessions with open button and stop button for each
    session.
    '''
    def __init__(self, notebook_manager):
        self.notebook_manager = notebook_manager
        super(NotebookManagerList, self).__init__()

    def create_ui(self):
        # Only list sessions that are currently running.
        sessions = collections.OrderedDict([(k, v)
                                            for k, v in self.notebook_manager
                                            .sessions.iteritems()
                                            if v.is_alive()])
        scroll_window = gtk.ScrolledWindow()
        scroll_window.set_size_request(480, 360)

        table = gtk.Table(len(sessions) + 1, 4)

        header_y_padding = 5
        x_padding = 20
        y_padding = 2

        for k, header in enumerate(['Directory', 'URL']):
            label = gtk.Label()
            label.set_markup('<b>%s</b>' % header)
            table.attach(label, k, k + 1, 0, 1,
                         xoptions=gtk.SHRINK,
                         yoptions=gtk.SHRINK,
                         xpadding=x_padding,
                         ypadding=header_y_padding)

        for i, (root, session) in enumerate(sessions.iteritems()):
            i += 1
            root = path(root)
            name_label = gtk.Label(root.name)
            name_label.set_tooltip_text(str(root))
            url_label = gtk.Label(session.address)

            stop_button = gtk.Button('Stop')
            stop_button.set_tooltip_text('Stop IPython notebook for directory %s'
                                         % root)
            open_button = gtk.Button('Open')
            open_button.set_tooltip_text('Open IPython notebook for directory %s'
                                         % root)

            def open_session(button, session):
                webbrowser.open_new_tab(session.address)

            def stop_session(button, session, widgets):
                session.stop()
                for widget in widgets:
                    table.remove(widget)

            open_button.connect('clicked', open_session, session)
            stop_button.connect('clicked', stop_session, session,
                                (name_label, url_label, open_button,
                                 stop_button))

            for k, widget in enumerate((name_label, url_label, open_button,
                                        stop_button)):
                if isinstance(widget, gtk.Button):
                    x_padding_k = 0
                else:
                    x_padding_k = x_padding
                table.attach(widget, k, k + 1, i, i + 1,
                             xoptions=gtk.SHRINK,
                             yoptions=gtk.SHRINK,
                             xpadding=x_padding_k,
                             ypadding=y_padding)
        self.table = table
        scroll_window.add_with_viewport(table)
        self.widget.pack_start(scroll_window, False, False, 0)


def add_filters(dialog, filters):
    for f in filters:
        filter_text = gtk.FileFilter()
        filter_text.set_name(f['name'])
        if 'mime_type' in f:
            mime_types = f['mime_type']
            if isinstance(mime_types, types.StringTypes):
                mime_types = [mime_types]
            for mime_type in mime_types:
                filter_text.add_mime_type(mime_type)
        elif 'pattern' in f:
            patterns = f['pattern']
            if isinstance(patterns, types.StringTypes):
                patterns = [patterns]
            for pattern in patterns:
                print 'add pattern: "%s"' % pattern
                filter_text.add_pattern(pattern)
        dialog.add_filter(filter_text)
