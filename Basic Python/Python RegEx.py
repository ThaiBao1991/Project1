# -****************************** Python RegEx
print("-********************** Python RegEx")

# RegEx in Python
print("-********************** RegEx in Python")
import re
#Check if the string starts with "The" and ends with "Spain":
txt = "The rain in Spain"
x = re.search("^The.*Spain$", txt)
if x:
  print("YES! We have a match!")
else:
  print("No match")

# ****************************** Metacharacters
print("-********************** Metacharacters")
# []	A set of characters
print("-********************** []	A set of characters")
txt = "The rain in Spain"
#Find all lower case characters alphabetically between "a" and "m":
x = re.findall("[a-m]", txt)
print(x)

# \	Signals a special sequence (can also be used to escape special characters)
print("-********************** \	Signals a special sequence (can also be used to escape special characters)")
txt = "That will be 59 dollars"
#Find all digit characters:
x = re.findall("\d", txt)
print(x)

# .	Any character (except newline character)
print("-********************** .	Any character (except newline character)")
txt = "hello planet"
#Search for a sequence that starts with "he", followed by two (any) characters, and an "o":
x = re.findall("he..o", txt)
print(x)

# ^	Starts with
print("-********************** ^	Starts with")
txt = "hello planet"
#Check if the string starts with 'hello':
x = re.findall("^hello", txt)
if x:
  print("Yes, the string starts with 'hello'")
else:
  print("No match")

# $	Ends with
print("-********************** $	Ends with")
#Check if the string ends with 'planet':
x = re.findall("planet$", txt)
if x:
  print("Yes, the string ends with 'planet'")
else:
  print("No match")

# *	Zero or more occurrences
print("-********************** *	Zero or more occurrences")
txt = "hello planet"
#Search for a sequence that starts with "he", followed by 0 or more  (any) characters, and an "o":
x = re.findall("he.*o", txt)
print(x)

# +	One or more occurrences
print("-********************** +	One or more occurrences")
txt = "hello planet"
#Search for a sequence that starts with "he", followed by 1 or more  (any) characters, and an "o":
x = re.findall("he.+o", txt)
print(x)

# ?	Zero or one occurrences
print("-********************** ?	Zero or one occurrences")
txt = "hello planet"
#Search for a sequence that starts with "he", followed by 0 or 1  (any) character, and an "o":
x = re.findall("he.?o", txt)
print(x)
#This time we got no match, because there were not zero, not one, but two characters between "he" and the "o"

# {}	Exactly the specified number of occurrences
print("-********************** {}	Exactly the specified number of occurrences")
txt = "hello planet"
#Search for a sequence that starts with "he", followed excactly 2 (any) characters, and an "o":
x = re.findall("he.{2}o", txt)
print(x)

# |	Either or
print("-********************** |	Either or")
txt = "The rain in Spain stays mainly in the plain!"
#Check if the string contains either "falls" or "stays":
x = re.findall("falls|stays", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# ********************************* Special Sequences
print("-********************** Special Sequences")
# \A	Returns a match if the specified characters are at the beginning of the string
print("-********************** \A	Returns a match if the specified characters are at the beginning of the string")
#Check if the string starts with "The":
x = re.findall("\AThe", txt)
print(x)
if x:
  print("Yes, there is a match!")
else:
  print("No match")

"""  \b	Returns a match where the specified characters are at the beginning or at the end of a word
 (the "r" in the beginning is making sure that the string is being treated as a "raw string")
 r lúc trước khi bắt đầu để thể hiện chuỗi là một chuỗi thô raw string
"""
print("-********************** \b	")
txt = "The rain in Spain"
#Check if "ain" is present at the beginning of a WORD:
x = re.findall(r"\bain", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

txt = "The rain in Spain"
#Check if "ain" is present at the end of a WORD:
x = re.findall(r"ain\b", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

"""  Returns a match where the specified characters are present, but NOT at the beginning (or at the end) of a word
(the "r" in the beginning is making sure that the string is being treated as a "raw string")
r lúc trước khi bắt đầu để thể hiện chuỗi là một chuỗi thô raw string
"""
print("-********************** \B	")
txt = "The rain in Spain"
#Check if "ain" is present, but NOT at the beginning of a word:
x = re.findall(r"\Bain", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

txt = "The rain in Spain"
#Check if "ain" is present, but NOT at the end of a word:
x = re.findall(r"ain\B", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# \d	Returns a match where the string contains digits (numbers from 0-9)
print("-********************** \d	Returns a match where the string contains digits (numbers from 0-9)")
txt = "The rain in Spain"
#Check if the string contains any digits (numbers from 0-9):
x = re.findall("\d", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# \D	Returns a match where the string DOES NOT contain digits
print("-********************** \D	Returns a match where the string DOES NOT contain digits")
txt = "The rain in Spain"
#Return a match at every no-digit character:
x = re.findall("\D", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# \s	Returns a match where the string contains a white space character
print("-********************** \s	Returns a match where the string contains a white space character")
txt = "The rain in Spain"
#Return a match at every white-space character:
x = re.findall("\s", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# \S	Returns a match where the string DOES NOT contain a white space character
print("-********************** \S	Returns a match where the string DOES NOT contain a white space character")
txt = "The rain in Spain"
#Return a match at every NON white-space character:
x = re.findall("\S", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# \w	Returns a match where the string contains any word characters (characters from a to Z, digits from 0-9, and the underscore _ character)
print("-***** \w	Returns a match where the string contains any word characters (characters from a to Z, digits from 0-9, and the underscore _ character)")
txt = "The rain in Spain"
#Return a match at every word character (characters from a to Z, digits from 0-9, and the underscore _ character):
x = re.findall("\w", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# \W	Returns a match where the string DOES NOT contain any word characters)
print("-***** \W	Returns a match where the string DOES NOT contain any word characters")
txt = "The rain in Spain"
#Return a match at every NON word character (characters NOT between a and Z. Like "!", "?" white-space etc.):
x = re.findall("\W", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# \Z	Returns a match if the specified characters are at the end of the string
print("-***** \Z	Returns a match if the specified characters are at the end of the string")
txt = "The rain in Spain"
#Check if the string ends with "Spain":
x = re.findall("Spain\Z", txt)
print(x)
if x:
  print("Yes, there is a match!")
else:
  print("No match")

# ******************************************* Sets
print("-******************************* Sets")
# [arn]	Returns a match where one of the specified characters (a, r, or n) is present
print("-[arn]	Returns a match where one of the specified characters (a, r, or n) is present")
txt = "The rain in Spain"
#Check if the string has any a, r, or n characters:
x = re.findall("[arn]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# [a-n]	Returns a match for any lower case character, alphabetically between a and n
print("[a-n]	Returns a match for any lower case character, alphabetically between a and n")
txt = "The rain in Spain"
#Check if the string has any characters between a and n:
x = re.findall("[a-n]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# [^arn]	Returns a match for any character EXCEPT a, r, and n
print("[^arn]	Returns a match for any character EXCEPT a, r, and n")
txt = "The rain in Spain"
#Check if the string has other characters than a, r, or n:
x = re.findall("[^arn]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# [0123]	Returns a match where any of the specified digits (0, 1, 2, or 3) are present
print("[0123]	Returns a match where any of the specified digits (0, 1, 2, or 3) are present")
txt = "The rain in Spain"
#Check if the string has any 0, 1, 2, or 3 digits:
x = re.findall("[0123]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# [0-9]	Returns a match for any digit between 0 and 9
print("[0-9]	Returns a match for any digit between 0 and 9")
txt = "8 times before 11:45 AM"
#Check if the string has any digits:
x = re.findall("[0-9]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# [0-5][0-9]	Returns a match for any two-digit numbers from 00 and 59
print("[0-5][0-9]	Returns a match for any two-digit numbers from 00 and 59")
txt = "8 times before 11:45 AM"
#Check if the string has any two-digit numbers, from 00 to 59:
x = re.findall("[0-5][0-9]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# [a-zA-Z]	Returns a match for any character alphabetically between a and z, lower case OR upper case
print("[a-zA-Z]	Returns a match for any character alphabetically between a and z, lower case OR upper case")
txt = "8 times before 11:45 AM"
#Check if the string has any characters from a to z lower case, and A to Z upper case:
x = re.findall("[a-zA-Z]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# [+]	In sets, +, *, ., |, (), $,{} has no special meaning, so [+] means: return a match for any + character in the string
print("[+]	In sets, +, *, ., |, (), $,{} has no special meaning, so [+] means: return a match for any + character in the string")
txt = "8 times before 11:45 AM"
#Check if the string has any + characters:
x = re.findall("[+]", txt)
print(x)
if x:
  print("Yes, there is at least one match!")
else:
  print("No match")

# ************************************** findall()
print("-***************** findall()")
txt = "The rain in Spain"
x = re.findall("ai", txt)
print(x)

txt = "The rain in Spain"
x = re.findall("Portugal", txt)
print(x)

# ************************************** search()
print("-***************** search()")
txt = "The rain in Spain"
x = re.search("\s", txt)
print("The first white-space character is located in position:", x.start()) 

txt = "The rain in Spain"
x = re.search("Portugal", txt)
print(x)

# ************************************** split()
print("-***************** split()")
#Split the string at every white-space character:
txt = "The rain in Spain"
x = re.split("\s", txt)
print(x)

#Split the string at the first white-space character:
txt = "The rain in Spain"
x = re.split("\s", txt, 1)
print(x)

# ************************************** sub()
print("-***************** sub()")
#Replace all white-space characters with the digit "9":
txt = "The rain in Spain"
x = re.sub("\s", "9", txt)
print(x)

txt = "The rain in Spain"
x = re.sub("\s", "9", txt, 2)
print(x)

# ************************************** Match Object
print("-***************** Match Object")
#The search() function returns a Match object:
txt = "The rain in Spain"
x = re.search("ai", txt)
print(x)

#Search for an upper case "S" character in the beginning of a word, and print its position:
txt = "The rain in Spain"
x = re.search(r"\bS\w+", txt)
print(x.span())

#The string property returns the search string: 
txt = "The rain in Spain"
x = re.search(r"\bS\w+", txt)
print(x.string)

#Search for an upper case "S" character in the beginning of a word, and print the word:
txt = "The rain in Spain"
x = re.search(r"\bS\w+", txt)
print(x.group())