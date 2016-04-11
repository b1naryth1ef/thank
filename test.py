from thank import Connection, Model
from thank.fields import *

conn = Connection(db="test")


class User(Model):
    class Meta:
        conn = conn

    username = StringField()
    password = StringField()


if not User.table_exists():
    User.table_create()

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
