# -*- coding: utf-8 -*-

"""
    pygtkhelpers.gthreads
    ~~~~~~~~~~~~~~~~~~~~~

    Helpers for integration of aysnchronous behaviour in PyGTK.

    .. warning::

        in order to get well-behaved threading, run :function:`initial_setup`
        as early as possible (befor doing any gui operations

    :copyright: 2005-2010 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""
from __future__ import with_statement
import functools
import threading
import thread
import Queue as queue
import gobject
import sys
import warnings

from gtk import gdk
import gtk


def initial_setup():
    """
    * set up gdk threading
    * enter it
    * set up glib mainloop threading

    .. versionchanged:: 0.18
        Do not execute ``gdk.threads_enter()``.

        ``gdk.threads_enter()/gdk.threads_leave()`` should only be used to wrap
        GTK code blocks.

        See `What are the general tips for using threads with PyGTK?
        <http://faq.pygtk.org/index.py?req=show&file=faq20.001.htp>`_.
    """
    warnings.warn('Use ', DeprecationWarning)
    gdk.threads_init()
    gobject.threads_init()  # the glib mainloop doesn't love us else


class AsyncTask(object):
    """Perform lengthy tasks without delaying the UI loop cycle.

    AsyncTask removes the boilerplate of deferring a task to a thread and
    receiving intermittent feedback from the thread. It handles creating and
    starting a thread for the task, and forcing any user interface calls to be
    pushed to the GTK main loop from the thread, thus ensuring against
    insanity which invariably ensues if this precaution is not taken.

    It is also assumed that each action that the async worker performs cancels
    the old one (if it's still working), thus there's no problem when the task
    takes too long.  You can either extend this class or pass two callable
    objects through its constructor.

    The first one is the 'work_callback' this is where the lengthy
    operation must be performed. This object may return an object or a group
    of objects, these will be passed onto the second callback 'loop_callback'.
    You must be aware on how the argument passing is done. If you return an
    object that is not a tuple then it's passed directly to the loop callback.
    If you return `None` no arguments are supplied. If you return a tuple
    object then these will be the arguments sent to the loop callback.

    The loop callback is called inside Gtk+'s main loop and it's where you
    should stick code that affects the UI.
    """
    def __init__(self, work_callback=None, loop_callback=None, daemon=True):
        gobject.threads_init()  # the glib mainloop doesn't love us else
        self.counter = 0
        self.daemon = daemon

        if work_callback is not None:
            self.work_callback = work_callback
        if loop_callback is not None:
            self.loop_callback = loop_callback

    def start(self, *args, **kwargs):
        """Start the task.

        This is:
            * not threadsave
            * assumed to be called in the gtk mainloop
        """
        args = (self.counter,) + args
        thread = threading.Thread(
                target=self._work_callback,
                args=args, kwargs=kwargs
                )
        thread.setDaemon(self.daemon)
        thread.start()

    def work_callback(self):
        pass

    def loop_callback(self):
        pass

    def _work_callback(self, counter, *args, **kwargs):
        ret = self.work_callback(*args, **kwargs)
        # tuple necessary cause idle_add wont allow more args
        gobject.idle_add(self._loop_callback, (counter, ret))

    def _loop_callback(self, vargs):
        counter, ret = vargs
        if counter != self.counter:
            return

        if ret is None:
            ret = ()
        if not isinstance(ret, tuple):
            ret = (ret,)
        with gdk.lock:
            self.loop_callback(*ret)


class GeneratorTask(AsyncTask):
    """
    The difference between this task and AsyncTask
    is that the `work` callback returns a generator.
    For each value the generator yields
    the `loop` callback is called inside Gtk+'s main loop.

    :param work: callback that returns results
    :param loop: callback inside the gtk thread
    :keyword priority: gtk priority the loop callback will have
    :keyword pass_generator:
        will pass the generator instance
        as `generator_task` to the worker callback

    A simple example::

        def work():
            for i in range(10000):
                yield i

        def loop(val):
            print val

        gt = GeneratorTask(work, loop)
        gt.start()
        import gtk
        gtk.main()
    """
    def __init__(self, work_callback, loop_callback, complete_callback=None,
                 priority=gobject.PRIORITY_DEFAULT_IDLE,
                 pass_generator=False):
        AsyncTask.__init__(self, work_callback, loop_callback)
        self.priority = priority
        self._complete_callback = complete_callback
        self._pass_generator = pass_generator

    def _work_callback(self, counter, *args, **kwargs):
        self._stopped = False
        if self._pass_generator:
            kwargs = kwargs.copy()
            kwargs['generator_task'] = self
        for ret in self.work_callback(*args, **kwargs):
            # XXX: what about checking self.counter?
            if self._stopped:
                thread.exit()
            gobject.idle_add(self._loop_callback, (counter, ret),
                             priority=self.priority)
        if self._complete_callback is not None:
            def idle(callback=self._complete_callback):
                with gdk.lock:
                    callback()
            gobject.idle_add(self._complete_callback,
                             priority=self.priority)

    def stop(self):
        self._stopped = True

    @property
    def is_stopped(self):
        return self._stopped


def gcall(func, *args, **kwargs):
    """
    Calls a function, with the given arguments inside Gtk's main loop.
    Example::
        gcall(lbl.set_text, "foo")

    If this call would be made in a thread there could be problems, using
    it inside Gtk's main loop makes it thread safe.
    """
    def idle():
        with gdk.lock:
            return bool(func(*args, **kwargs))
    return gobject.idle_add(idle)


def invoke_in_mainloop(func, *args, **kwargs):
    """
    Invoke a function in the mainloop, pass the data back.
    """
    results = queue.Queue()

    @gcall
    def run():
        try:
            data = func(*args, **kwargs)
            results.put(data)
            results.put(None)
        except BaseException:  # XXX: handle
            results.put(None)
            results.put(sys.exc_info())
            raise

    data = results.get()
    exception = results.get()

    if exception is None:
        return data
    else:
        tp, val, tb = results.get()
        raise tp, val, tb


def gtk_threadsafe(func):
    '''
    Decorator to make wrapped function threadsafe by forcing it to execute
    within the GTK main thread.

    .. versionadded:: 0.18

    .. versionchanged:: 0.22
        Add support for keyword arguments in callbacks by supporting functions
        wrapped by `functools.partial()`.  Also, ignore callback return value
        to prevent callback from being called repeatedly indefinitely.  See the
        `gobject.idle_add() documentation`_ for further information.


    .. _`gobject.idle_add() documentation`: http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--idle-add


    Parameters
    ----------
    func : function or functools.partial
    '''
    # Set up GDK threading.
    # XXX This must be done to support running multiple threads in GTK
    # applications.
    gtk.gdk.threads_init()

    # Support
    wraps_func = func.func if isinstance(func, functools.partial) else func

    @functools.wraps(wraps_func)
    def _gtk_threadsafe(*args):
        def _no_return_func(*args):
            func(*args)

        gobject.idle_add(_no_return_func, *args)

    return _gtk_threadsafe
