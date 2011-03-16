import unittest

import pymodel as model

class Sub(model.Model):
    s = model.String(thrift_id=1)
    
    def __eq__(self, other):
        if self and other:
            return self.s == other.s
        else:
            return not self and not other


class Parent(model.RootObjectModel):
    s = model.String(thrift_id=1)
    b = model.Object(Sub, thrift_id=2)

    def __eq__(self, other):
        return self.s == other.s and self.b == other.b


class TestInheritance(unittest.TestCase):
    def test_instanciation(self):
        p = Parent()

    def test_assignment(self):
        p = Parent()
        b = Sub()
        p.b = b

    def test_equality(self):
        p = Parent()
        p.s = 'abc'

        b = Sub()
        b.s = 'def'

        p.b = b

        data = p.serialize(self.serializer)

        o = Parent.deserialize(self.serializer, data)

        self.assertEquals(p, o)


import pymodel.test
pymodel.test.setup(globals())
