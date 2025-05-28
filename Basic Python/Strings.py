# -***********************Strings
print("Hello")
print('hello')

a= "Hello"
print(a)

print('-********** Multiline Strings')
a = """ I can do anything if I want, 
If I try, I will make the world """
print (a)


print('-********** Strings are Arrays')
a = "Hi My Friends"
print(a[1])


print('-********** Looping Through a String')
for x in "banana":
    print(x)

print('-********** String len')
a = "Hi My Friends"
print(len(a))

print('-********** Check String')
a = "Hi My Friends"
print("My" in a)

print('-********** If')
a = "Hi My Friends"
if("My" in a):
    print("Yes, 'My' is pressent. ")

print('-********** Check If NOT')
a = "Hi My Friends"
print("expensive" not in a)


# *************************** Slicing Strings
b = "Hello, World!"
print(b[2:5])

# Slice From the Start
b = "Hello, World!"
print(b[:5])

# Slice To the End
b = "Hello, World!"
print(b[2:])

# Negative Indexing
b = "Hello, World!"
print(b[-5:-2])

# *************************** Modify Strings
# Upper Case
a = "Hello, World!"
print(a.upper())

# Lower Case
a = "Hello, World!"
print(a.lower())

# Remove Whitespace
a = " Hello, World! "
print(a.strip()) # returns "Hello, World!"

# Replace String
a = "Hello, World!"
print(a.replace("H", "J"))

# Split String
a = "Hello, World!"
print(a.split(",")) # returns ['Hello', ' World!']

# *************************** String Concatenations
# String Concatenation
a = "Hello"
b = "World"
c = a + b
print(c)

a = "Hello"
b = "World"
c = a + " " + b
print(c)

# *************************** Format - Strings
# String Format
age = 36
txt = "My name is John, and I am {}"
print(txt.format(age))

quantity = 3
itemno = 567
price = 49.95
myorder = "I want {} pieces of item {} for {} dollars."
print(myorder.format(quantity, itemno, price))

quantity = 3
itemno = 567
price = 49.95
myorder = "I want to pay {2} dollars for {0} pieces of item {1}."
print(myorder.format(quantity, itemno, price))

# *************************** Escape Characters
# Escape Character
print("- ***************** Escape Character")
txt = "We are the so-called \"Vikings\" from the north."
print(txt)

# \'	Single Quote
txt = 'It\'s alright.'
print(txt) 

# \\	Backslash
txt = "This will insert one \\ (backslash)."
print(txt) 

# \n	New Line
txt = "Hello\nWorld!"
print(txt) 

# \r	Carriage Return
txt = "Hello\rYes!"
print(txt) 

# \t	Tab
txt = "Hello\tWorld!"
print(txt) 

# \b	Backspace
txt = "Hello \bWorld!"
print(txt) 

# \f	Form Feed

# \ooo	Octal value
txt = "\110\145\154\154\157"
print(txt) 

# \xhh	Hex value
txt = "\x48\x65\x6c\x6c\x6f"
print(txt) 


# *************************** String Methods
# String Methods
print("- ***************** String Methods")
# capitalize()	Converts the first character to upper case
print("-********* capitalize()")
txt = "hello"
txt= txt.capitalize()
print(txt)

# casefold()	Converts string into lower case
print("-********* casefold()")
txt = "Hello, And Welcome To My World!"
x = txt.casefold()
print(x)

# center()	Returns a centered string
print("-********* Center()")
txt = "banana"
x = txt.center(20)
print(x)

txt = "banana"
x = txt.center(20, "O")
print(x)

# count() 		Returns the number of times a specified value occurs in a string
print("-********* count()")
txt = "I love apples, apple are my favorite fruit"
x = txt.count("apple")
print(x)

txt = "I love apples, apple are my favorite fruit"
x = txt.count("apple", 10, 24)
print(x)

# encode()	Returns an encoded version of the string
print("-********* encode()")
txt = "My name is Ståle"
x = txt.encode()
print(x)

txt = "My name is Ståle"

print(txt.encode(encoding="ascii",errors="backslashreplace"))
print(txt.encode(encoding="ascii",errors="ignore"))
print(txt.encode(encoding="ascii",errors="namereplace"))
print(txt.encode(encoding="ascii",errors="replace"))
print(txt.encode(encoding="ascii",errors="xmlcharrefreplace"))

# endswith()	Returns true if the string ends with the specified value
print("-********* endswith()")
txt = "Hello, welcome to my world."
x = txt.endswith(".")
print(x)

txt = "Hello, welcome to my world."
x = txt.endswith("my world.")
print(x)

txt = "Hello, welcome to my world."
x = txt.endswith("my world.", 5, 11)
print(x)

# expandtabs()	Sets the tab size of the string
print("-********* expandtabs()")
txt = "H\te\tl\tl\to"
x =  txt.expandtabs(2)
print(x)

txt = "H\te\tl\tl\to"

print(txt)
print(txt.expandtabs())
print(txt.expandtabs(2))
print(txt.expandtabs(4))
print(txt.expandtabs(10))

# find()	Searches the string for a specified value and returns the position of where it was found
print("-********* find()")
txt = "Hello, welcome to my world."
x = txt.find("welcome")
print(x)

txt = "Hello, welcome to my world."
x = txt.find("e")
print(x)

txt = "Hello, welcome to my world."
x = txt.find("e", 5, 10)
print(x)

txt = "Hello, welcome to my world."
print(txt.find("q"))

# format()	Formats specified values in a string
print("-********* format()")
txt = "For only {price:.2f} dollars!"
print(txt.format(price = 49))

txt1 = "My name is {fname}, I'm {age}".format(fname = "John", age = 36)
txt2 = "My name is {0}, I'm {1}".format("John",36)
txt3 = "My name is {}, I'm {}".format("John",36)

print(txt1)
print(txt2)
print(txt3)

#Use "<" to left-align the value:
txt = "We have {:<8} chickens."
print(txt.format(49))

#Use ">" to right-align the value:
txt = "We have {:>8} chickens."
print(txt.format(49))

#Use "^" to center-align the value:
txt = "We have {:^8} chickens."
print(txt.format(49))

#Use "=" to place the plus/minus sign at the left most position:
txt = "The temperature is {:=8} degrees celsius."
print(txt.format(-5))

#Use "+" to always indicate if the number is positive or negative:
txt = "The temperature is between {:+} and {:+} degrees celsius."
print(txt.format(-3, 7))

#Use "-" to always indicate if the number is negative (positive numbers are displayed without any sign):
txt = "The temperature is between {:-} and {:-} degrees celsius."
print(txt.format(-3, 7))

#Use " " (a space) to insert a space before positive numbers and a minus sign before negative numbers:
txt = "The temperature is between {: } and {: } degrees celsius."
print(txt.format(-3, 7))

#Use "," to add a comma as a thousand separator:
txt = "The universe is {:,} years old."
print(txt.format(13800000000))

#Use "_" to add a underscore character as a thousand separator:
txt = "The universe is {:_} years old."
print(txt.format(13800000000))

#Use "b" to convert the number into binary format:
txt = "The binary version of {0} is {0:b}"
print(txt.format(7))

#Use "d" to convert a number, in this case a binary number, into decimal number format:
txt = "We have {:d} chickens."
print(txt.format(0b101))

#Use "e" to convert a number into scientific number format (with a lower-case e):
txt = "We have {:e} chickens."
print(txt.format(5))

#Use "E" to convert a number into scientific number format (with an upper-case E):
txt = "We have {:E} chickens."
print(txt.format(5))

#Use "f" to convert a number into a fixed point number, default with 6 decimals, but use a period followed by a number to specify the number of decimals:

txt = "The price is {:.2f} dollars."
print(txt.format(45))
#without the ".2" inside the placeholder, this number will be displayed like this:
txt = "The price is {:f} dollars."
print(txt.format(45))

#Use "F" to convert a number into a fixed point number, but display inf and nan as INF and NAN:
x = float('inf')
txt = "The price is {:F} dollars."
print(txt.format(x))
#same example, but with a lower case f:
txt = "The price is {:f} dollars."
print(txt.format(x))

#Use "o" to convert the number into octal format:
txt = "The octal version of {0} is {0:o}"
print(txt.format(10))

#Use "x" to convert the number into Hex format:
txt = "The Hexadecimal version of {0} is {0:x}"
print(txt.format(255))

#Use "X" to convert the number into upper-case Hex format:
txt = "The Hexadecimal version of {0} is {0:X}"
print(txt.format(255))

#Use "%" to convert the number into a percentage format:
txt = "You scored {:%}"
print(txt.format(0.25))
#Or, without any decimals:
txt = "You scored {:.0%}"
print(txt.format(0.25))
