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
        self.called_count = 0
        object.connect(signal, self)

    def __call__(self, *k):
        print 'call'
        self.called = k
        self.called_count += 1

