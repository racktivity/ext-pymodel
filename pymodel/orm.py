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

import sqlalchemy
import sqlalchemy.orm

import pymodel

LOGGER = logging.getLogger(__name__)

def patch_sqlalchemy():
    '''Monkey-patch SQLAlchemy for PyModel compatibility'''

    LOGGER.info('Patching SQLAlchemy')

    def patched_instance_dict(obj):
        '''Patched version of sqlalchemy.orm.attributes.instance_dict'''

        if isinstance(obj, pymodel.Model):
            return obj._pymodel_store
        else:
            return obj.__dict__

    sqlalchemy.orm.attributes.instance_dict = patched_instance_dict

patch_sqlalchemy()
del patch_sqlalchemy

_metadata = sqlalchemy.MetaData()

_ATTR_COL_MAP = {
    pymodel.String: sqlalchemy.Text(),
    pymodel.GUID: sqlalchemy.String(36),
    pymodel.Integer: sqlalchemy.Integer(),
    pymodel.Float: sqlalchemy.Float(),
    pymodel.Boolean: sqlalchemy.Boolean(),
    # pymodel.Enumeration: sqlalchemy.Text(),
}

def _map_table(type_):
    '''Create a mapping for the given PyModel model type

    This procedure creates `sqlalchemy.Table` instances, based on metadata found
    in the PyModel metadata of the given `type_`. This table, as well as any
    table referred to (e.g. when using `pymodel.Object` fields) is registered
    with the SQLAlchemy mapper, and returned, so client code can generate the
    database tables if required.

    :param type_: Type to map
    :type type_: subclass of `pymodel.Model`

    :return: List of created tables
    :rtype: iterable of `sqlalchemy.Table`
    '''

    meta = type_.PYMODEL_MODEL_INFO
    name = meta.name.lower()

    LOGGER.debug('Mapping type %s' % name)

    tables = []

    table = sqlalchemy.Table(name, _metadata)

    is_rootobject = issubclass(type_, pymodel.RootObjectModel)

    if not is_rootobject:
        col = sqlalchemy.Column('_pymodel_id', sqlalchemy.Integer(),
            primary_key=True)
        table.append_column(col)

    properties = {}

    for attr in meta.attributes:
        attr_name = attr.name
        attr_ = attr.attribute

        if type(attr_) != pymodel.Object:
            primary_key = is_rootobject and attr_name == 'guid'
            col = sqlalchemy.Column(attr_name, _ATTR_COL_MAP[type(attr_)],
                primary_key=primary_key)

            table.append_column(col)
        else:
            sub = _map_table(attr.attribute.type_)
            tables.extend(sub)

            sub_name = attr_.type_.PYMODEL_MODEL_INFO.name

            col = sqlalchemy.Column('%s_id' % attr_name, sqlalchemy.Integer(),
                sqlalchemy.ForeignKey('%s._pymodel_id' % sub_name.lower()))
            table.append_column(col)
            rel = sqlalchemy.orm.relationship(attr_.type_, uselist=False)
            properties[attr_name] = rel

        prop = sqlalchemy.orm.attributes.create_proxied_attribute(attr)
        prop_inst = prop(type_, attr_name, attr, None)
        delattr(type_, attr_name)
        setattr(type_, attr_name, prop_inst)

    sqlalchemy.orm.mapper(type_, table, properties=properties)

    tables.append(table)

    return tuple(tables)

def register(type_):
    '''Register a given root object model type with the SQLAlchemy ORM

    This procedure registers a given `pymodel.RootObjectModel` subtype with the
    SQLAlchemy ORM subsystem, and creates tables and mappings for any type
    referred to, e.g. when using `pymodel.Object` fields.

    It returns an iterable of the generated tables, so these can be created in a
    database system by client code.

    :param type_: Root object type to register
    :type type_: subclass of `pymodel.RootObjectModel`
    :return: Generated tables
    :rtype: iterable of `sqlalchemy.Table`
    '''

    if not issubclass(type_, pymodel.RootObjectModel):
        raise TypeError('Only pymodel.RootObjectModel types can be registered')

    LOGGER.info('Registering type %s' % type_.PYMODEL_MODEL_INFO.name)

    return _map_table(type_)
