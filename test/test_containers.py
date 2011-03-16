import unittest

import pymodel as model
from pymodel.utils import compare_content

class ContentComparisonMixin:
    def __eq__(self, other):
        return compare_content(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)


class B(model.Model):
    pass

# Push in ContentComparisonMixin as base since the Model metaclass doesn't like
# us to inherit directly.
# This is a hack.
B.__bases__ = tuple([ContentComparisonMixin, ] + list(B.__bases__))

class A(model.RootObjectModel):
    l = model.List(model.Object(B), thrift_id=1)
    i = model.List(model.Integer(), thrift_id=2)

A.__bases__ = tuple([ContentComparisonMixin, ] + list(A.__bases__))


class TestList(unittest.TestCase):
    def _cmp(self, value):
        data = value.serialize(self.serializer)

        n = value.__class__.deserialize(self.serializer, data)
        self.assertEquals(type(value), type(n))
        self.assertEquals(value, n)

    def test_instanciation(self):
        o = A()

        self._cmp(o)

    def test_assignment(self):
        o = A()
        b = o.l.new()
        o.l.append(b)

        o.i = [1, 2, 3]

        self._cmp(o)

class C(model.RootObjectModel):
    d = model.Dict(model.Object(B), thrift_id=1)
    e = model.Dict(model.String(), thrift_id=2)
C.__bases__ = tuple([ContentComparisonMixin, ] + list(C.__bases__))

class TestDict(unittest.TestCase):
    def _cmp(self, value):
        data = value.serialize(self.serializer)

        n = value.__class__.deserialize(self.serializer, data)
        self.assertEquals(type(value), type(n))
        self.assertEquals(value, n)

    def test_instanciation(self):
        o = C()

        self._cmp(o)

    def test_serialisation(self):
        o = C()
        o.d['test1'] = B()
        o.d['test2'] = B()
        o.e['test3'] = '3tset'
        o.e['test4'] = '4tset'
        o.e['test3'] = 'test3'

        self._cmp(o)

    def test_type(self):
        o = C()

        def _set1():
            o.e['abc'] = 123

        def _set2():
            o.d[123] = 'abc'

        self.assertRaises(TypeError, _set1)
        self.assertRaises(TypeError, _set2)


import pymodel.test
pymodel.test.setup(globals())

if __name__ == '__main__':
    unittest.main()
