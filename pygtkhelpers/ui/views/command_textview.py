import os
import re
import sys

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
                loop.stop() # end loop.run_forever()

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

