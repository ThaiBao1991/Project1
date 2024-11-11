# -****************************** Python Dates
print("-********************** Python Dates")
import datetime
x = datetime.datetime.now()
print(x)

# Date Output
x = datetime.datetime.now()
print(x.year)
print(x.strftime("%A"))

# Creating Date Objects
x = datetime.datetime(2020, 5, 17)
print(x)

# --------------------- The strftime() Method
x = datetime.datetime(2023, 11, 19)

# %a	Weekday, short version	Wed
print(x.strftime("%a"))

# %A	Weekday, full version	Wednesday
print(x.strftime("%A"))

# %w	Weekday as a number 0-6, 0 is Sunday	3
print(x.strftime("%w"))

# %d	Day of month 01-31	31
print(x.strftime("%d"))

# %b	Month name, short version	Dec
print(x.strftime("%b"))

# %B	Month name, full version	December
print(x.strftime("%B"))

# %m	Month as a number 01-12	12
print(x.strftime("%m"))

# %y	Year, short version, without century	18
print(x.strftime("%y"))

# %Y	Year, full version	2018
print(x.strftime("%Y"))

# %H	Hour 00-23	17
print(x.strftime("%Y"))

# %I	Hour 00-12	05
print(x.strftime("%I"))

# %p	AM/PM	PM
print(x.strftime("%p"))

# %M	Minute 00-59	41
print(x.strftime("%M"))

# %S	Second 00-59	08
print(x.strftime("%S"))

# %f	Microsecond 000000-999999	548513
print(x.strftime("%f"))

# %z	UTC offset	+0100
print(x.strftime("%z"))

# %Z	Timezone	CST
print(x.strftime("%Z"))

# %j	Day number of year 001-366	365
print(x.strftime("%j"))

# %U	Week number of year, Sunday as the first day of week, 00-53	52
print(x.strftime("%U"))

# %W	Week number of year, Monday as the first day of week, 00-53	52
print(x.strftime("%W"))

# %c	Local version of date and time	Mon Dec 31 17:41:00 2018
print(x.strftime("%c"))

# %C	Century	20
print(x.strftime("%C"))

# %x	Local version of date	12/31/18
print(x.strftime("%x"))

# %X	Local version of time	17:41:00
print(x.strftime("%X"))

# %%	A % character	%
print(x.strftime("%%"))

# %G	ISO 8601 year	2018
print(x.strftime("%G"))

# %G	%u	ISO 8601 weekday (1-7)	1
print(x.strftime("%u"))

# %V	ISO 8601 weeknumber (01-53)	01
print(x.strftime("%V"))