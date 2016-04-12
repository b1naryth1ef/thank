import time

from thank import Connection, Model
from thank.fields import *

conn = Connection(db="test")


class UserSettings(Model):
    a = BooleanField(default=False)
    b = IntegerField(default=0)
    c = FloatField(default=time.time)


class User(Model, conn.use):
    username = StringField()
    password = StringField()
    # settings = EmbeddedField(UserSettings)


class Login(Model, conn.use):
    user = ReferenceField(User)
    ip = StringField()


# Create tables
for table in [User, Login]:
    print 'creating %s' % table
    if not table.table_exists():
        table.table_create()
    else:
        table.objects.delete()


def test_basic():
    # Delete all users
    User.objects.delete()

    # Create test users
    for i in range(100):
        User.create(username="test{}".format(i), password=("z" * i))

    # Get all users
    print User.objects.all()

    # Get the count the proper way
    print User.objects.count()

    # Get a single user
    test1 = User.objects.filter_by(username="test1").only(User.id).one()
    print test1

    # Update a single user
    test1.password = 'ayy'
    test1.save()
    print User.objects.filter_by(password='ayy').count()

    # Delete a single user
    test1.delete()
    print User.objects.filter_by(password='ayy').count()


def test_complex():
    user = User.create(username="jeff", password="jeff")

    for i in range(50):
        Login.create(user=user, ip="127.0.0.{}".format(i))

    # print Login.objects.filter_by(user=user).count()
    # print Login.objects.filter(Login.ip == "127.0.0.1").one()
    print Login.objects.filter(Login.ip == "127.0.0.1").join(User).one().user.id
    print Login.objects.filter_by(ip="127.0.0.1").join(User).one().user.id
    # print Login.objects.filter_by(ip="127.0.0.1").only(Login.id, User.username).one().user.__dict__

# test_basic()
test_complex()
