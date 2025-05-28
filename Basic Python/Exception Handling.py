# -****************************** Exception Handling
print("-********************** Exception Handling")
#The try block will generate an error, because x is not defined:
try:
  print(x)
except:
  print("An exception occurred")

# -Many Exceptions
print("-Many Exceptions")
#The try block will generate a NameError, because x is not defined:
try:
  print(x)
except NameError:
  print("Variable x is not defined")
except:
  print("Something else went wrong")

# -Else
print("-Else")
# Else sẽ thực hiện khi không có lỗi
#The try block does not raise any errors, so the else block is executed:
try:
  print("Hello")
except:
  print("Something went wrong")
else:
  print("Nothing went wrong")


# -Finally
print("-Finally")
# Finally sẽ luôn thực hiện cho dù có lỗi hay không
#The finally block gets executed no matter if the try block raises any errors or not:
try:
  print(x)
except:
  print("Something went wrong")
finally:
  print("The 'try except' is finished")

#The try block will raise an error when trying to write to a read-only file:
try:
  f = open("demofile.txt")
  try:
    f.write("Lorum Ipsum")
  except:
    print("Something went wrong when writing to the file")
  finally:
    f.close()
except:
  print("Something went wrong when opening the file")  

# -Raise an exception
print("-Raise an exception")
x = -1
if x < 0:
  raise Exception("Sorry, no numbers below zero")

x = "hello"
if not type(x) is int:
  raise TypeError("Only integers are allowed")