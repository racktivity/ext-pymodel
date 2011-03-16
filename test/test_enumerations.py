import unittest

try:
    from pylabs.baseclasses.BaseEnumeration import BaseEnumeration
except ImportError:
    import nose
    raise nose.SkipTest('No pylabs support on this system')

import pymodel as model

class MyEnum(BaseEnumeration):
    @classmethod
    def _initItems(cls):
        cls.registerItem('foo')
        cls.registerItem('bar')
        cls.finishItemRegistration()

class EnumModel(model.RootObjectModel):
    e = model.Enumeration(MyEnum, thrift_id=1)

class TestEnumerations(unittest.TestCase):
    def test_instanciation(self):
        i = EnumModel()

    def test_assignment(self):
        i = EnumModel()
        i.e = MyEnum.FOO
        i.e = MyEnum.BAR

    def test_serialization(self):
        i = EnumModel()
        i.e = MyEnum.FOO

        j = EnumModel.deserialize(self.serializer, i.serialize(self.serializer))
        self.assert_(i is not j)
        self.assert_(i.e is j.e)


import pymodel.test
pymodel.test.setup(globals())
