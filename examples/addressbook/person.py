"""
    person
    ~~~~~~

    a simple class repressenting a person for usage in exampes
"""
from datetime import datetime, date


class Person(object):
    def __init__(self, name, surname, email):
        self.name = name
        self.surname = surname
        self.email = email


    def __repr__(self):
        return '<Person %r, %r - %r>'%(self.name, self.surname, self.email)
