from fablab.core import load, save
import json

# from fablab.core import Foo
# from fablab.pickle_ref import _dumps, _loads
# import pickletools

# save, load = _dumps, _loads
# first = Foo(1)
# second = Foo(2)
# first.b = [1, 2, second]
# second.b = first

# serialized = dumps(first)
# print(serialized)

my_list = ["FIRST"]
a = ("first", my_list)
my_list.append(a)
a = (1, 2, [1, (a, a)])
fs = save(a)

print(json.dumps(fs, indent=4))

new = load(fs)

print(a)
print(new)
