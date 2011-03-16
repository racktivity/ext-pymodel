import unittest

import pymodel as model

class BarModel(model.Model):
    baz = model.String(thrift_id=1)

class FooModel(model.RootObjectModel):
    field = model.Object(BarModel, thrift_id=1)

class TestObjectField(unittest.TestCase):
    def setUp(self):
        self.instance = FooModel()

    def tearDown(self):
        delattr(self, 'instance')

    def test_none_equality(self):
        self.assert_(self.instance.field is not None)

    def test_bool_value(self):
        self.assert_(not self.instance.field)

    def test_new_attribute(self):
        self.assert_(hasattr(self.instance.field, 'new'))
        self.assert_(callable(self.instance.field.new))

    def test_assignment(self):
        self.instance.field = self.instance.field.new(baz='test')
        self.assert_(self.instance.field)
        self.assertEquals(self.instance.field.baz, 'test')
        self.instance.field.baz = 'test2'
        self.assertEquals(self.instance.field.baz, 'test2')

    def test_none_assignment(self):
        self.assert_(not self.instance.field)

        self.instance.field = self.instance.field.new(baz='test3')
        self.assert_(self.instance.field)
        self.assertEqual(self.instance.field.baz, 'test3')
        first_field = self.instance.field

        self.instance.field = None
        self.assert_(not self.instance.field)
        self.assert_(self.instance.field is not None)

        self.instance.field = self.instance.field.new()
        self.assertNotEqual(self.instance.field, first_field)


import pymodel.test
pymodel.test.setup(globals())
