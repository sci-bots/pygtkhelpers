import functools
import os
import re
import sys

import gobject
import gtk
import trollius as asyncio

from ...delegates import SlaveView
from ...utils import gsignal, refresh_gui


class CommandTextView(SlaveView):
    # Emit signal when data is written `(fd, data)`.
    gsignal('data-written', int, str)

    def create_ui(self):
        self.scroll = gtk.ScrolledWindow()
        self.scroll.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        self.scroll.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC

        self.text_view = gtk.TextView()
        self.scroll.add_with_viewport(self.text_view)
        self.text_view.props.editable = False

        buf = self.text_view.get_buffer()
        red = '#cb2027'
        green = '#059748'
        buf.create_tag('red', foreground=red)
        buf.create_tag('green', foreground=green)
        buf.create_tag('mono', font='Consolas 10')

        self.widget.pack_start(self.scroll)
        self.widget.show_all()

    def run(self, command, *args, **kwargs):
        self_ = self

        class SubprocessProtocol(asyncio.SubprocessProtocol):
            def pipe_data_received(self, fd, data):
                self_._write(fd, re.sub(r'(\r?\n)+', r'\1', data))

            def connection_lost(self, exc):
                loop.stop()  # end loop.run_forever()

        if os.name == 'nt':
            # For subprocess' pipes on Windows
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
        else:
            loop = asyncio.get_event_loop()

        try:
            if kwargs.pop('shell', False):
                proc = loop.subprocess_shell(SubprocessProtocol, command)
            else:
                proc = loop.subprocess_exec(SubprocessProtocol, *command)

            def _refresh_gui():
                refresh_gui()
                loop.call_soon(_refresh_gui)

            loop.call_soon(_refresh_gui)
            transport, protocol = loop.run_until_complete(proc)
            loop.run_forever()
        except Exception, exception:
            self._write(2, str(exception))
        else:
            return transport.get_returncode()
        finally:
            loop.close()

    def _write(self, fd, data):
        self.emit('data-written', fd, data)

        if fd == 1:
            sys.stdout.write(data)
        elif fd == 2:
            sys.stderr.write(data)

        buf = self.text_view.get_buffer()
        buf.insert(buf.get_end_iter(), data)

        color = 'red' if fd == 2 else 'green'

        start = buf.get_iter_at_mark(buf.get_insert())
        end = buf.get_iter_at_mark(buf.get_insert())
        start.backward_chars(len(data))
        buf.apply_tag_by_name(color, start, end)
        buf.apply_tag_by_name('mono', start, end)
        return True


def get_run_command_dialog(command, shell=False, title='', data_callback=None,
                           parent=None, **kwargs):
    '''
    Launch command in a subprocess and create a dialog window to monitor the
    output of the process.

    Parameters
    ----------
    command : list or str
        Subprocess command to execute.
    shell : bool, optional
        If :data:`shell` is ``False``, :data:`command` **must** be a
        :class:`list`.

        If :data:`shell` is ``True``, :data:`command` **must** be a
        :class:`str`.
    title : str, optional
        Title for dialog window and initial contents of main label.
    data_callback : func(dialog, command_view, fd, data), optional
        Callback function called when data is available for one of the file
        descriptors.

        The :data:`fd` callback parameter is 1 for ``stdout`` and 2 for
        ``stderr``.
    **kwargs
        Additional keyword arguments are interpreted as dialog widget property
        values and are applied to the dialog widget.

    Returns
    -------
    gtk.Dialog
        Dialog with a progress bar and an expandable text view to monitor the
        output of the specified :data:`command`.

        .. note::

            Subprocess is launched before returning dialog.
    '''
    dialog = gtk.Dialog(title=title or None, parent=parent)
    dialog.set_size_request(540, -1)
    for key, value in kwargs.iteritems():
        setattr(dialog.props, key, value)

    dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_OK)
    dialog.set_default_response(gtk.RESPONSE_OK)

    content_area = dialog.get_content_area()
    label = gtk.Label(title)
    label.props.xalign = .1
    content_area.pack_start(label, expand=False, fill=True, padding=10)

    progress_bar = gtk.ProgressBar()

    expander = gtk.Expander('Details')

    # Resize window based on whether or not expander is open.
    expander.connect('activate', functools
                     .partial(lambda w, e, *args:
                              w.set_size_request(540, -1 if e.props.expanded
                                                 else 480), dialog))

    command_view = CommandTextView()
    if data_callback is not None:
        command_view.connect('data-written', functools.partial(data_callback,
                                                               dialog))

    expander.add(command_view.widget)

    content_area.pack_start(progress_bar, expand=False)
    content_area.pack_start(expander, expand=True, fill=True)

    button = dialog.get_action_area().get_children()[0]
    content_area.show_all()

    def _run_command(label, progress_bar, button, view, command, shell):
        button.props.sensitive = False
        text_buffer = command_view.text_view.get_buffer()
        text_buffer.delete(*text_buffer.get_bounds())

        def _pulse(*args):
            progress_bar.pulse()
            return True

        timeout_id = gobject.timeout_add(250, _pulse)
        command_view.run(command, shell=shell)
        gobject.source_remove(timeout_id)
        progress_bar.set_fraction(1.)
        button.props.sensitive = True
        label.set_markup('{} <b>done</b>.'.format(title))

    gobject.idle_add(_run_command, label, progress_bar, button, command_view,
                     command, shell)
    return dialog


if __name__ == '__main__':
    command = r"dir C:\Windows\System32"
    title = 'List system files...'

    # Update label to display each `.exe` file encountered.
    cre_exe_file = re.compile(r'(?P<filename>\w+\.exe)')

    def data_callback(dialog, command_view, fd, data):
        for match_i in cre_exe_file.finditer(data):
            (dialog.get_content_area().get_children()[0]
             .set_markup('`.exe` file: <b>{}</b>'
                         .format(match_i.group('filename'))))

    response = get_run_command_dialog(command, title=title, shell=True,
                                      resizable=False,
                                      data_callback=data_callback).run()
