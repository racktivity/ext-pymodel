import inspect
import logging
import weakref

from pymodel.fields import Field, GUID, String

LOGGER = logging.getLogger(__name__)

GUIDField = GUID()
GUIDField.name = 'guid'
VersionField = GUID()
VersionField.name = 'version'
CreationDateField = String()
CreationDateField.name = 'creationdate'
BaseVersionField = GUID()
BaseVersionField.name = '_baseversion'
DEFAULT_FIELDS = (GUIDField, VersionField, CreationDateField, BaseVersionField)

class _PymodelModelAttribute(object):
    def __init__(self, name, attribute):
        self.name = name
        self.attribute = attribute

class _PymodelModelInfo(object):
    def __init__(self, name, attrs):
        self.type = None
        self.name = name

        self.attributes = self.read_attributes(attrs)
        self.defaults = self.read_defaults(self.attributes)

    def read_attributes(self, attrs):
        LOGGER.debug('Creating attribute info for %s' % self.name)
        return tuple(_PymodelModelAttribute(*info) for info in
                attrs.iteritems() if isinstance(info[1], Field))

    def read_defaults(self, attrs):
        return dict((attr.name, attr.attribute.kwargs['default'])
            for attr in attrs
            if 'default' in attr.attribute.kwargs)

    def __str__(self):
        return 'Pymodel model info for %s' % self.name


class ModelMeta(type):
    def __new__(cls, name, bases, attrs, allow_slots=False):
        LOGGER.info('Generating model type %s' % name)
        try:
            Model
            RootObjectModel
        except NameError:
            return type.__new__(cls, name, bases, attrs)

        if not allow_slots and '__slots__' in attrs:
            raise RuntimeError(
                'Don\'t set a \'__slots__\' value on model classes')

        assert 'guid' not in attrs, \
                'Model classes should have no explicit \'guid\' attribute'
        assert 'version' not in attrs, \
                'Model classes should have no explicit \'version\' attribute'
        assert '_baseversion' not in attrs, \
                'Model classes should have no explicit \'_baseversion\' attribute'
        assert 'creationdate' not in attrs, \
                'Model classes should have no explicit' \
                'creationdate\' attribute'

        for field in DEFAULT_FIELDS:
            attrs[field.name] = field

        attrs['PYMODEL_MODEL_INFO'] = _PymodelModelInfo(name, attrs)

        for attr_name, attr in attrs.iteritems():
            if isinstance(attr, Field) and attr not in DEFAULT_FIELDS:
                attr.name = attr_name

        import pymodel.model
        extra_bases = set(bases).difference(
            set((pymodel.Model, pymodel.RootObjectModel, )))
        if extra_bases:
            raise RuntimeError(
                'A model should only inherit from Model or RootObjectModel, '
                'not %s' % repr([base.__name__ for base in extra_bases]))

        for base in bases:
            if not hasattr(base, '__slots__'):
                raise RuntimeError('Base class %s has no __slots__ defined' %
                                   base.__name__)

        # Calculate and set __slots__ - see 'Datamodel' in the Python
        # language reference
        # '_sa_instance_state' is something we need for SQLAlchemy ORM
        # compatibilty (see pymodel.orm)
        slots = ['_pymodel_store', '__weakref__', '_sa_instance_state', ]
        for attrname, attr in attrs.iteritems():
            if isinstance(attr, Field):
                slots.append(attrname)
        attrs['__slots__'] = tuple(slots)

        type_ = type.__new__(cls, name, bases, attrs)
        # Do we actually need this?
        type_.PYMODEL_MODEL_INFO.type = weakref.proxy(type_)

        # Perform one more __slots__ check, just to be sure (other metaclasses
        # might fool us)
        for base in inspect.getmro(type_):
            if base is not object and not hasattr(base, '__slots__'):
                raise RuntimeError('Base class %s has no __slots__ defined' % \
                                   base.__name__)

        return type_


class Model(object):
    __metaclass__ = ModelMeta
    __slots__ = ('_pymodel_store', )

    # Make PyLint happy, set by metaclass
    PYMODEL_MODEL_INFO = None

    def __init__(self, **kwargs):
        self._pymodel_store = self.PYMODEL_MODEL_INFO.defaults.copy()

        attribute_names = set(attr.name for attr in
                self.PYMODEL_MODEL_INFO.attributes)

        for key, value in kwargs.iteritems():
            if key not in attribute_names:
                raise ValueError('Unknown attribute %s' % key)

            setattr(self, key, value)

    def __str__(self):
        d = dict()
        for attr in self.PYMODEL_MODEL_INFO.attributes:
            d[attr.name] = getattr(self, attr.name)

        return str(d)

    def __eq__(self, other):
        if self is other:
            return True

        if not type(self) is type(other):
            return NotImplemented

        if not self.version or not self.guid:
            return False

        return self.guid == other.guid and self.version == other.version

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if not self.version:
            return hash(self.guid) if self.guid else object.__hash__(self)

        return hash((self.guid, self.version, ))
           
class RootObjectModel(Model):
    __slots__ = tuple()

    def serialize(self, serializer):
        return serializer.serialize(self)

    @classmethod
    def deserialize(cls, deserializer, data):
        return deserializer.deserialize(cls, data)
