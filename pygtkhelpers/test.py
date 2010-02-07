# -*- coding: utf-8 -*-

"""
    pygtkhelpers.test
    ~~~~~~~~~~~~~~~~~

    Assistance for unittesting pygtk

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

class CheckCalled(object):
    """Utility to check whether a signal has been emitted
    """
    def __init__(self, object, signal):
        self.called = None
        object.connect(signal, self)

    def __call__(self, *k):
        self.called = k

