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

import sqlalchemy

import pymodel
import pymodel.orm

class Address(pymodel.Model):
    street = pymodel.String(thrift_id=1)
    number = pymodel.String(thrift_id=2)
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


tables = pymodel.orm.register(User)

conn = sqlalchemy.create_engine('sqlite://')
conn.echo = True
SessionMaker = sqlalchemy.orm.sessionmaker(bind=conn)
session = SessionMaker()

print session.query(User).filter(User.age==26)

for table in tables:
    table.create(conn, checkfirst=True)

addr = Address(street='Main Street', number=1, postal_code=9000,
    city='Capital', country='Belgium')
user = User(
    first_name='Nicolas', last_name='T.', age=26, f=3.1415, b=True,
    address=addr)
user.guid = str(uuid.uuid4())
user._baseversion = str(uuid.uuid4())


session.add(user)
session.commit()

for u in session.query(User) \
    .filter(User.age >= 20) \
    .filter(User.age < 30) \
    .filter(User.last_name.like('T%')) \
    .all():
    print u
    print u.first_name
    print u.address.street

    session.delete(u)

session.commit()

import base64
from pymodel.serializers import ThriftSerializer

print base64.encodestring(u.serialize(ThriftSerializer))
