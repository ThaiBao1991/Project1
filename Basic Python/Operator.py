# -***********************Operators
print("-*********************** Python Arithmetic Operators")
# +	Addition	x + y
x = 5
y = 3
print(x + y)
# -	Subtraction	x - y
x = 5
y = 3
print(x - y)
# *	Multiplication	x * y
x = 5
y = 3
print(x * y)
# /	Division	x / y
x = 12
y = 3
print(x / y)
# %	Modulus	x % y
x = 5
y = 2
print(x % y)
# **	Exponentiation	x ** y
x = 2
y = 5
print(x ** y) #same as 2*2*2*2*2
# //	Floor division	x // y
x = 15
y = 2
print(x // y)
#the floor division // rounds the result down to the nearest whole number

print("-*********************** Python Assignment Operators")
# =	x = 5	x = 5
x = 5
print(x)

# +=	x += 3	x = x + 3
x = 5
x += 3
print(x)

# -=	x -= 3	x = x - 3
x = 5
x -= 3
print(x)

# *=	x *= 3	x = x * 3
x = 5
x *= 3
print(x)

# /=	x /= 3	x = x / 3
x = 5
x /= 3
print(x)

# %=	x %= 3	x = x % 3
x = 5
x%=3
print(x)

# //=	x //= 3	x = x // 3
x = 5
x//=3
print(x)

# **=	x **= 3	x = x ** 3
x = 5
x **= 3
print(x)

# &=	x &= 3	x = x & 3  ( 1-1 = 1, 1-0=0, 0-1=0, 0-0=0)
x = 5
print (bin(x)) # 00000000000000000000000000000101
x &= 3
print(bin(3)) #00000000000000000000000000000011
print("& : " + str(x)) #00000000000000000000000000000001

# ~	    x = ~a (a=1-a , 1=>0 , 0 => 1)
x = 5
x = ~x
print("~ : " + str(x))

# |=	x |= 3	x = x | 3 (1-1 = 1, 1-0=1, 0-1=1, 0-0=0)
x = 5
x |= 3
print("| : " + str(x))

# ^=	x ^= 3	x = x ^ 3 return (a and not b) or (not a and b) (1-0=1 , 1-1=0, 0-0 =0, 0-1=1)
x = 5
x ^= 3
print("^ : " + str(x))

# >>=	x >>= 3	x = x >> 3 ( Add 0 to right)
x = 20 
print (bin(x)) # 00000000000000000000000000010100
x >>= 3 # 00000000000000000000000000010
print(">> : " + str(f"{x:08b}"))

# <<=	x <<= 3	x = x << 3 ( Add 0 to left)
x = 5 # 00000000000000000000000000000101
x <<= 3 # 00000000000000000000000000101000 = 1*2^5 + 2^3 = 32 + 8 = 40
print("<< : " + str(f"{x:032b}"))


print("-******************** Python Comparison Operators")
# ==	Equal	x == y
x = 5
y = 3
print(x == y)
# returns False because 5 is not equal to 3

# !=	Not equal	x != y
x = 5
y = 3
print(x != y)
# returns True because 5 is not equal to 3


# >	Greater than	x > y
x = 5
y = 3
print(x > y)
# returns True because 5 is greater than 3


# <	Less than	x < y
x = 5
y = 3
print(x < y)
# returns False because 5 is not less than 3

# >=	Greater than or equal to	x >= y
x = 5
y = 3
print(x >= y)
# returns True because five is greater, or equal, to 3

# <=	Less than or equal to	x <= y
x = 5
y = 3
print(x <= y)
# returns False because 5 is neither less than or equal to 3

print("-******************** Python Logical Operators")
# and 	Returns True if both statements are true	x < 5 and  x < 10
x = 5
print(x > 3 and x < 10)
# returns True because 5 is greater than 3 AND 5 is less than 10

# or	Returns True if one of the statements is true	x < 5 or x < 4
x = 5
print(x > 3 or x < 4)
# returns True because one of the conditions are true (5 is greater than 3, but 5 is not less than 4)

# not	Reverse the result, returns False if the result is true	not(x < 5 and x < 10)
x = 5
print(not(x > 3 and x < 10))
# returns False because not is used to reverse the result

print("-******************** Python Identity Operators")
# is 	Returns True if both variables are the same object	x is y
x = ["apple", "banana"]
y = ["apple", "banana"]
z = x
print(x is z)
# returns True because z is the same object as x
print(x is y)
# returns False because x is not the same object as y, even if they have the same content
print(x == y)
# to demonstrate the difference betweeen "is" and "==": this comparison returns True because x is equal to y

# is not	Returns True if both variables are not the same object	x is not y
x = ["apple", "banana"]
y = ["apple", "banana"]
z = x
print(x is not z)
# returns False because z is the same object as x
print(x is not y)
# returns True because x is not the same object as y, even if they have the same content
print(x != y)
# to demonstrate the difference betweeen "is not" and "!=": this comparison returns False because x is equal to y

print("-******************** Python Bitwise Operators")
# & 	AND	Sets each bit to 1 if both bits are 1	x & y
print(6 & 3)



"""
The & operator compares each bit and set it to 1 if both are 1, otherwise it is set to 0:

6 = 0000000000000110
3 = 0000000000000011
--------------------
2 = 0000000000000010
====================

Decimal numbers and their binary values:
0 = 0000000000000000
1 = 0000000000000001
2 = 0000000000000010
3 = 0000000000000011
4 = 0000000000000100
5 = 0000000000000101
6 = 0000000000000110
7 = 0000000000000111
"""

# |	OR	Sets each bit to 1 if one of two bits is 1	x | y
print(6 | 3)



"""
The | operator compares each bit and set it to 1 if one or both is 1, otherwise it is set to 0:

6 = 0000000000000110
3 = 0000000000000011
--------------------
7 = 0000000000000111
====================

Decimal numbers and their binary values:
0 = 0000000000000000
1 = 0000000000000001
2 = 0000000000000010
3 = 0000000000000011
4 = 0000000000000100
5 = 0000000000000101
6 = 0000000000000110
7 = 0000000000000111
"""

# ^	XOR	Sets each bit to 1 if only one of two bits is 1	x ^ y
print(6 ^ 3)



"""
The ^ operator compares each bit and set it to 1 if only one is 1, otherwise (if both are 1 or both are 0) it is set to 0:

6 = 0000000000000110
3 = 0000000000000011
--------------------
5 = 0000000000000101
====================

Decimal numbers and their binary values:
0 = 0000000000000000
1 = 0000000000000001
2 = 0000000000000010
3 = 0000000000000011
4 = 0000000000000100
5 = 0000000000000101
6 = 0000000000000110
7 = 0000000000000111
"""

# ~	NOT	Inverts all the bits	~x
print(~3)



"""
The ~ operator inverts each bit (0 becomes 1 and 1 becomes 0).

Inverted 3 becomes -4:
 3 = 0000000000000011
-4 = 1111111111111100

Decimal numbers and their binary values:
 4 = 0000000000000100
 3 = 0000000000000011
 2 = 0000000000000010
 1 = 0000000000000001
 0 = 0000000000000000
-1 = 1111111111111111
-2 = 1111111111111110
-3 = 1111111111111101
-4 = 1111111111111100
"""

# <<	Zero fill left shift	Shift left by pushing zeros in from the right and let the leftmost bits fall off	x << 2
print(3 << 2)



"""
The << operator inserts the specified number of 0's (in this case 2) from the right and let the same amount of leftmost bits fall off:

If you push 00 in from the left:
 3 = 0000000000000011
becomes
12 = 0000000000001100

Decimal numbers and their binary values:
 0 = 0000000000000000
 1 = 0000000000000001
 2 = 0000000000000010
 3 = 0000000000000011
 4 = 0000000000000100
 5 = 0000000000000101
 6 = 0000000000000110
 7 = 0000000000000111
 8 = 0000000000001000
 9 = 0000000000001001
10 = 0000000000001010
11 = 0000000000001011
12 = 0000000000001100
"""

# >>	Signed right shift	Shift right by pushing copies of the leftmost bit in from the left, and let the rightmost bits fall off	x >> 2
print(8 >> 2)



"""
The >> operator moves each bit the specified number of times to the right. Empty holes at the left are filled with 0's.

If you move each bit 2 times to the right, 8 becomes 2:
 8 = 0000000000001000
becomes
 2 = 0000000000000010

Decimal numbers and their binary values:
 0 = 0000000000000000
 1 = 0000000000000001
 2 = 0000000000000010
 3 = 0000000000000011
 4 = 0000000000000100
 5 = 0000000000000101
 6 = 0000000000000110
 7 = 0000000000000111
 8 = 0000000000001000
 9 = 0000000000001001
10 = 0000000000001010
11 = 0000000000001011
12 = 0000000000001100
"""

