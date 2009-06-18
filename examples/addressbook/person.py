"""
    person
    ~~~~~~

    a simple class repressenting a person for usage in exampes
"""
from __future__ import with_statement


try: #XXX
    import json
except:
    import simplejson as json

class Person(object):
    def __init__(self, name, surname, email):
        self.name = name
        self.surname = surname
        self.email = email


    def __repr__(self):
        return '<Person %r, %r - %r>'%(self.name, self.surname, self.email)


def to_json(listing, target):
    output = []
    for item in listing:
        output.append({
            'name': item.name,
            'surname': item.surname,
            'email':item.email
        })
    with open(target, 'w') as outf:
        json.dump(output, outf, indent=2)


def from_json(file):
    with open(file) as inf:
        data = json.load(inf)
    for item in data:
        yield Person(item['name'], item['surname'], item['email'])
