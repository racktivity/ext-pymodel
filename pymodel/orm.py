# <License type="Aserver BSD" version="2.0">
#
# Copyright (c) 2005-2011, Aserver NV.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# * Neither the name Aserver nor the names of other contributors
#   may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ASERVER "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL ASERVER BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

'''
The `pymodel.orm` module provides some bridging code between PyModel and the
SQLAlchemy_ ORM mapper.

.. _SQLAlchemy: http://www.sqlalchemy.org
'''

import logging
import operator

import sqlalchemy
import sqlalchemy.orm

HAS_CREATE_PROXIED_ATTRIBUTE = False
HAS_PROXIED_ATTRIBUTE_FACTORY = False

if hasattr(sqlalchemy.orm.attributes, "create_proxied_attribute"):
    HAS_CREATE_PROXIED_ATTRIBUTE = True
elif hasattr(sqlalchemy.orm.attributes, "proxied_attribute_factory"):
    HAS_PROXIED_ATTRIBUTE_FACTORY = True

import pymodel

from pymodel.serializers._thrift import generate_dict_spec, thrift_write
from pymodel.serializers._thrift import thrift_read, ThriftObjectWrapper

LOGGER = logging.getLogger(__name__)


class DictWrapper:
    '''
    Class wrapping dictionaries, used for storing dicts containing Pymodel objects / fields in DB
    '''
    def __init__ (self, name, d):
        '''
        Constructor
        
        @param name: Name of the object (same as in thrift spec of the dict)
        @param d: The dictionary that is wrapped
        '''
        setattr(self, name, d)
            
class CustomDictPickler:
    '''
    Class used by the sqlalchemy PickleType to pickle/unpickle dicts containing Pymodel objects / Fields 
    '''
    def __init__(self, name, spec):
        '''
        Constructor 
        
        @param name: Name of the attribute in the spec containing the dictionary 
        @param spec: The thrift spec used to serialize the dictionary
        '''
        self.name = name
        self.spec = spec
    
    def loads(self, serialized):
        '''
        Deserialize a dictionary
        
        @param serialized The serialized dictionary
        @return The desereliazied dict
        '''
        object_ = DictWrapper(self.name, dict())
        thrift_read(object_, self.spec, serialized)
        return getattr(object_, self.name)

    def dumps(self, obj, protocol=None):
        '''
        Serialize a dictionary
        
        @param obj: The dictionary to serialize
        @param protocol: Not used (just here to respect the Pickle interface)
        @return The serialized dictionary
        '''
        obj_ = DictWrapper(self.name, obj)
        data = thrift_write(obj_, self.spec)
        return data 


class CustomEnumPickler:
    '''
     Class used by the sqlalchemy PickleType to pickle/unpickle dicts
    '''
    def __init__(self, enumType):
        '''
        Constructor 
        
        '''
        self.enumType = enumType
    
    def loads(self, serialized):
        '''
        Deserialize an enumeration instance
        
        @param serialized: The serialized enumeration
        @return The desereliazied dict        
        '''
        return self.enumType.getByName(serialized)
    
    def dumps(self, obj, protocol=None):
        '''
        Serialize an enumeration
        
        @param obj: The enumeration to serialize
        @param protocol: Not used (just here to respect the Pickle interface)
        @return The serialized enumeration
        '''
        return str(obj)
    
def patch_sqlalchemy():
    '''Monkey-patch SQLAlchemy for PyModel compatibility'''

    LOGGER.info('Patching SQLAlchemy')

    def patched_instance_dict(obj):
        '''Patched version of sqlalchemy.orm.attributes.instance_dict'''

        if isinstance(obj, pymodel.Model):
            # HACK!
            # Somehow we get in this code path, without the 'obj' constructor
            # being called before (the instance has no '_pymodel_store'
            # attribute, which is set in the pymodel.model.Model constructor
            # only). This seems to be SQLAlchemy-related. In case this happens,
            # we brute-force constructor execution. Ugly, dirty, terrible, but
            # no way around for now.
            # See test.test_orm:TestORM.test_not_initialized
            if not hasattr(obj, '_pymodel_store'):
                type(obj).__init__(obj)

            return obj._pymodel_store #pylint: disable-msg=W0212
        else:
            return obj.__dict__

    sqlalchemy.orm.attributes.instance_dict = patched_instance_dict

patch_sqlalchemy()
del patch_sqlalchemy

# Make pylint happy
if False:
    pymodel.String = object
    pymodel.GUID = object
    pymodel.Integer = object
    pymodel.Float = object
    pymodel.Boolean = object
    pymodel.Object = object
    pymodel.List = object

_ATTR_COL_MAP = {
    pymodel.String: sqlalchemy.Text(),
    pymodel.GUID: sqlalchemy.String(36),
    pymodel.Integer: sqlalchemy.Integer(),
    pymodel.Float: sqlalchemy.Float(),
    pymodel.Boolean: sqlalchemy.Boolean(),
    pymodel.DateTime: sqlalchemy.DateTime() 
}

BASIC_ATTR_TYPES = (
    pymodel.String, pymodel.GUID,
    pymodel.Integer, pymodel.Float,
    pymodel.Boolean, pymodel.DateTime,
#    pymodel.Enumeration
)

class Context(object):
    '''Context used by the SQLAlchemy ORM glue

    An instance of this should be used to group related PyModel models when
    being registered. These will share a `sqlalchemy.MetaData` instance.
    '''

    def __init__(self, metadata=None):
        '''Initialize a new `Context` instance

        A `sqlalchemy.MetaData` instance can be provided to be used as metadata
        for this context. If no metadata instance is provided, a new one will
        be created and used.

        :param metadata: Optional metadata instance to use
        :type metadata: `sqlalchemy.MetaData`
        '''

        self._metadata = metadata if metadata is not None \
            else sqlalchemy.MetaData()

    def register(self, type_):
        '''Register a given root object model type with the SQLAlchemy ORM

        This procedure registers a given `pymodel.RootObjectModel` subtype with
        the SQLAlchemy ORM subsystem, and creates tables and mappings for any
        type referred to, e.g. when using `pymodel.Object` fields.

        It returns an iterable of the generated tables, so these can be created
        in a database system by client code.

        :param type_: Root object type to register
        :type type_: subclass of `pymodel.RootObjectModel`
        :return: Generated tables
        :rtype: iterable of `sqlalchemy.Table`
        '''

        if not issubclass(type_, pymodel.RootObjectModel):
            raise TypeError(
                'Only pymodel.RootObjectModel types can be registered')

        LOGGER.info('Registering type %s' % type_.PYMODEL_MODEL_INFO.name)

        return _map_table(self._metadata, type_)

    metadata = property(fget=operator.attrgetter('_metadata'),
        doc='Retrieve the `sqlalchemy.MetaData` instance used by this context')


def _map_table(metadata, type_, parent=None):
    '''Create a mapping for the given PyModel model type

    This procedure creates `sqlalchemy.Table` instances, based on metadata
    found in the PyModel metadata of the given `type_`. This table, as well as
    any table referred to (e.g. when using `pymodel.Object` fields) is
    registered with the SQLAlchemy mapper, and returned, so client code can
    generate the database tables if required.

    :param metadata: SQLAlchemy metadata object to work with
    :type metadata: `sqlalchemy.MetaData`
    :param type_: Type to map
    :type type_: subclass of `pymodel.Model`

    :return: List of created tables
    :rtype: iterable of `sqlalchemy.Table`
    '''

    meta = type_.PYMODEL_MODEL_INFO
    name = meta.name.lower()

    LOGGER.debug('Mapping type %s' % name)

    tables = []

    table = sqlalchemy.Table(name, metadata)

    is_rootobject = issubclass(type_, pymodel.RootObjectModel)

    if not is_rootobject:
        col = sqlalchemy.Column('_pymodel_id', sqlalchemy.Integer(),
            primary_key=True)
        table.append_column(col)

    if parent:
        parent_id_type, parent_name = parent
        col = sqlalchemy.Column('_pymodel_parent_id', parent_id_type,
            sqlalchemy.ForeignKey(parent_name))
        table.append_column(col)
    
    properties = {}

    if is_rootobject:
        # Push 'guid' to front
        attributes = [attr for attr in meta.attributes if attr.name == 'guid']
        attributes.extend(attr for attr in meta.attributes
            if attr.name != 'guid')
    else:
        attributes = meta.attributes

    for attr in attributes:
        attr_name = attr.name
        attr_ = attr.attribute

        if type(attr_) in BASIC_ATTR_TYPES:
            primary_key = is_rootobject and attr_name == 'guid'
            col = sqlalchemy.Column(attr_name, _ATTR_COL_MAP[type(attr_)],
                primary_key=primary_key)

            table.append_column(col)
        elif type(attr_) == pymodel.Object:
            sub = _map_table(metadata, attr.attribute.type_)
            tables.extend(sub)
            sub_name = attr_.type_.PYMODEL_MODEL_INFO.name
            col = sqlalchemy.Column('%s_id' % attr_name, sqlalchemy.Integer(),
                sqlalchemy.ForeignKey('%s._pymodel_id' % sub_name.lower()))
            table.append_column(col)
            rel = sqlalchemy.orm.relationship(attr_.type_, uselist=False)
            properties[attr_name] = rel
        elif type(attr_) == pymodel.List:
            sub = _map_table(metadata, attr.attribute.type_,
                (sqlalchemy.Integer if not is_rootobject
                    else sqlalchemy.String(36),
                '%s.%s' % (name,
                    'guid' if is_rootobject else '_pymodel_id')))

            tables.extend(sub)

            rel = sqlalchemy.orm.relationship(attr.attribute.type_)
            properties[attr_name] = rel

        elif type(attr_) == pymodel.Dict:
            # Rather 'crooked' type check
            # isinstance(attr_.type_, pymodel.Model) would have been better but for some reason is not working...
            if hasattr(attr_.type_, '_pymodel_store'  ) :
                f = pymodel.Object(attr_.type_) 
            else:
                f = attr_.type_ ()

            name = "%s_%s" % (name, attr_name)
            thrift_spec = generate_dict_spec(name, f)
            pickler = CustomDictPickler( name, thrift_spec)
            col = sqlalchemy.Column(attr_name, 
                                    sqlalchemy.PickleType(pickler=pickler))
            table.append_column(col)
        
        elif type(attr_) == pymodel.Enumeration:
            pickler = CustomEnumPickler(attr_.type_)
            col= sqlalchemy.Column(attr_name, sqlalchemy.PickleType(pickler=pickler) )
            table.append_column(col)
        
        else:
            raise NotImplementedError

        if HAS_PROXIED_ATTRIBUTE_FACTORY:
            prop = sqlalchemy.orm.attributes.proxied_attribute_factory(attr)
            prop_inst = prop(attr_name, attr, None, None)
        elif HAS_CREATE_PROXIED_ATTRIBUTE:
            prop = sqlalchemy.orm.attributes.create_proxied_attribute(attr)
            prop_inst = prop(type_, attr_name, attr, None)
        else:
            raise NotImplementedError

        delattr(type_, attr_name)
        setattr(type_, attr_name, prop_inst)

    sqlalchemy.orm.mapper(type_, table, properties=properties)

    tables.append(table)

    return tuple(tables)


