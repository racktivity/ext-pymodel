import timeit

try:
    import profilestats
except ImportError:
    pass

import pymodel
import pymodel.serializers

Thrift = pymodel.serializers.SERIALIZERS['thrift']
ThriftNative = pymodel.serializers.SERIALIZERS['_ThriftNative']
ThriftOptimized = pymodel.serializers.SERIALIZERS['_ThriftOptimized']

class User(pymodel.Model):
    first_name = pymodel.String(thrift_id=1)
    last_name = pymodel.String(thrift_id=2)
    age = pymodel.Integer(thrift_id=3)
    email = pymodel.List(pymodel.String(), thrift_id=4)

def run(s):
    u = User(
        first_name='Nicolas',
        last_name='Trangez',
        age=26,
        email=['nicolas incubaid com', 'ikke nicolast be']
    )

    d = s.serialize(u)
    u2 = s.deserialize(User, d)

    assert u2.first_name == u.first_name
    assert u2.last_name == u.last_name
    assert u2.age == u.age
    assert u2.email == u.email


def time(number):
    print 'Thrift:',
    t = timeit.Timer(
        'run(s)', 'from __main__ import run, Thrift as s')
    print t.timeit(number=number)

    print 'ThriftNative:',
    t = timeit.Timer(
        'run(s)', 'from __main__ import run, ThriftNative as s')
    print t.timeit(number=number)

    print 'ThriftOptimized:',
    t = timeit.Timer(
        'run(s)', 'from __main__ import run, ThriftOptimized as s')
    print t.timeit(number=number)

@profilestats.profile
def profile(count):
    for _ in xrange(count):
        run(Thrift)

if __name__ == '__main__':
    time(80000)

    if profilestats:
        runs = 1000
        print 'Creating profile (%d runs)' % runs
        profile(runs)
    else:
        print 'Unable to generate profile, install \'profilestats\''
