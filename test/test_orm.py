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

'''Basic testing script for `pymodel.orm`'''

import uuid
import unittest

import sqlalchemy

import pymodel
import pymodel.orm
import pymodel.serializers

class TestORM(unittest.TestCase):
    @staticmethod
    def _get_session():
        conn = sqlalchemy.create_engine('sqlite://')
        conn.echo = True

        SessionMaker = sqlalchemy.orm.sessionmaker(bind=conn)
        session = SessionMaker()

        return conn, session

    @staticmethod
    def _get_models():
        class Address(pymodel.Model):
            street = pymodel.String(thrift_id=1)
            number = pymodel.Integer(thrift_id=2)
            postal_code = pymodel.Integer(thrift_id=3)
            city = pymodel.String(thrift_id=4)
            country = pymodel.String(thrift_id=5)

        class User(pymodel.RootObjectModel):
            first_name = pymodel.String(thrift_id=1)
            last_name = pymodel.String(thrift_id=2)
            age = pymodel.Integer(thrift_id=3)
            f = pymodel.Float(thrift_id=4)
            b = pymodel.Boolean(thrift_id=5)
            address = pymodel.Object(Address, thrift_id=6)

        return User, Address

    def test_register(self):
        User, _ = self._get_models()
        c = pymodel.orm.Context()

        tables = c.register(User)

        self.assertEqual(len(tables), 2)

        _, s = self._get_session()
        s.query(User).filter(User.age == 26)

    def test_create_tables(self):
        User, _ = self._get_models()

        c = pymodel.orm.Context()
        tables = c.register(User)

        conn, _ = self._get_session()
        map(lambda t: t.create(conn), tables)

    def test_insert(self):
        User, Address = self._get_models()

        c = pymodel.orm.Context()
        tables = c.register(User)

        conn, s = self._get_session()
        map(lambda t: t.create(conn), tables)

        addr = Address(street='Main Street', number=1,
            postal_code=9000, city='Capital', country='Belgium')
        user = User(
            first_name='Nicolas', last_name='T.', age=26, f=3.1415, b=True,
            address=addr)

        user.guid = str(uuid.uuid4())

        s.add(user)
        s.commit()

    def test_query(self):
        User, Address = self._get_models()

        c = pymodel.orm.Context()
        tables = c.register(User)

        conn, s = self._get_session()
        map(lambda t: t.create(conn), tables)

        addr = Address(street='Main Street', number=1,
            postal_code=9000, city='Capital', country='Belgium')
        user = User(
            first_name='Nicolas', last_name='T.', age=26, f=3.1415, b=True,
            address=addr)

        user.guid = str(uuid.uuid4())

        s.add(user)
        s.commit()

        for u in s.query(User) \
            .filter(User.age >= 20) \
            .filter(User.age < 30) \
            .filter(User.last_name.like('T%')) \
            .all():

            self.assertEqual(u.first_name, 'Nicolas')
            self.assertEqual(u.age, 26)
            self.assertEqual(u.address.country, 'Belgium')

            s.delete(u)

    def test_serialization(self):
        User, Address = self._get_models()

        c = pymodel.orm.Context()
        c.register(User)

        addr = Address(street='Main Street', number=1,
            postal_code=9000, city='Capital', country='Belgium')
        user = User(
            first_name='Nicolas', last_name='T.', age=26, f=3.1415, b=True,
            address=addr)

        user.guid = str(uuid.uuid4())
        user.version = str(uuid.uuid4())

        serializer = pymodel.serializers.SERIALIZERS['_ThriftNative']
        data = user.serialize(serializer)
        user_ = User.deserialize(serializer, data)

        self.assertEqual(user_, user)