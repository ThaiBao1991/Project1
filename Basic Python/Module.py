# -****************************** Modules
print("-********************** Modules")
# Create And Use Module
import ModuleLibrary
ModuleLibrary.greeting("Jonathan")

# Variables in Module
a = ModuleLibrary.person1["age"]
print(a)

# Re-naming a Module
import ModuleLibrary as mx
a = mx.person1["age"]
print(a)

# Built-in Modules
import platform
x = platform.system()
print(x)

# Using the dir() Function
x = dir(platform)
print(x)

# Import From Module
from ModuleLibrary import person1
print (person1["age"])