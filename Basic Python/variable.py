import random

print('hello world')
if 5 >2 :
    print ('Five is greater than two!')

#***************This is comment
print('-****************This is commnen line')
"""
    This is a multiline comments
    comment1
    comment2
"""

#****************** Variable Value
x =5
y= "Bao"
Y="Thai"
print ('-***************Variable value')
print(x)
print(y)
print(Y)

#*************** Setting Variable Type Value
x= str(3)
y = int(3)
z = float (3)

print ('-*************Setting Variable Type value')
print (x)
print (y)
print (z)

# Type of Variable
print ('-*************Type of Variable')
print (type(x))
print (type(y))
print (type(z))

# Illegal Variable name 
myvar = "Bao"
my_var = "Bao"
_my_var = "Bao"
myVar = "Bao"
MYVAR = "Bao"
myvar2 = "Bao"

# Many Values To Multiple Varialbes
print ('-*************Many Values To Multiple Varialbes')
x,y,z = "Orange", "Banana","Cherry"
print(x)
print(y)
print(z)

print ('-*************One Value To Multiple Varialbes')
x =y =z = "Orange"
print(x)
print(y)
print(z)

print ('-*************Unpack a Collection')
fruits = ["apple","banana","candle"]
x,y,z = fruits
print(x)
print(y)
print(z)

# Output variables
print ("-****************Output Variables")
x = "Python is my language"
print (x)

print ("-****************combine String")
x= "Python"
y= "is"
z = "my"
t = "language"
print(x,y,z,t)
print(x+y+z+t)

x= 5
y=10
print(x+y)

x="Bao"
y=1
print(x,y)

# Global Variables
x =  "awesome"
def myfunc():
    print ("Python is " + x)
myfunc()

def myfunc():
    print ("-************ Example in block variable")
    x= "fantasic"
    print ("Python is " + x)
myfunc()
    
print ("Python is " + x)

print(random.randrange(1, 10))

#********************************* Python Casting
# Integer
print (int(1) == 1)
print (int(2.8) == 2)
print (int("12") == 12)
# Float
print (float(1) == 1.0)
print (float(2.8) == 2.8)
print (float("3") == 3.0)
print (float("4.2") == 4.2)
# String
print (str("s1") == 's1')
print (str(2) == '2')
print (str(3.0) == '3.0')
