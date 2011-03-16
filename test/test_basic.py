import unittest

import pymodel as model

class A(model.RootObjectModel):
    s = model.String(thrift_id=1)
    i = model.Integer(thrift_id=2)
    f = model.Float(thrift_id=3)
    bt = model.Boolean(thrift_id=4)
    bf = model.Boolean(thrift_id=5)

    def __eq__(self, other):
        return self.s == other.s and self.i == other.i and self.f == other.f

class TestModel(unittest.TestCase):
    def test_simple(self):
        A()

    def test_assign(self):
        a = A()
        a.s = 'string'
        a.i = 123
        a.f = 3.14159265
        a.bt = True
        a.bf = False

    def test_serialize(self):
        a = A()
        a.s = 'string'
        a.i = 123
        a.f = 3.14159265
        a.bt = True
        a.bf = False
        data = a.serialize(self.serializer)

        b = A.deserialize(self.serializer, data)
        self.assertEquals(a, b)

    def test_slots(self):
        a = A()
        self.assertRaises(AttributeError, setattr, a, 'j', 123)

    def test_empty_fields(self):
        class B(model.Model):
            i = model.Integer(thrift_id=1)

        class C(model.RootObjectModel):
            b = model.Object(B, thrift_id=1)

        inst = C()
        data = inst.serialize(self.serializer)
        inst2 = C.deserialize(self.serializer, data)

        self.assert_(not inst2.b)

    def test_int_assignment_to_string_field(self):
        class B(model.RootObjectModel):
            s = model.String(thrift_id=1)

        inst = B()
        self.assertRaises(TypeError, setattr, inst, 's', 123)

    def test_class_fields(self):
        self.assertEquals(None, A.s)

import pymodel.test
pymodel.test.setup(globals())
