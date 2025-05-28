# -****************************** Python Math
print("-********************** Python Math")
import math
# Built-in Math Functions
print("-********************** Built-in Math Functions")
x = min(5, 10, 25)
y = max(5, 10, 25)
print(x)
print(y)

x = abs(-7.25)
print(x)

x = pow(4, 3)
print(x)


# The Math Module
print("-********************** The Math Module")
x = math.sqrt(64)
print(x)

x = math.ceil(1.4)
y = math.floor(1.4)
print(x) # returns 2
print(y) # returns 1

x = math.pi
print(x)

# Math Module Reference
print("-********************** Math Module Reference")
# math.acos()	Returns the arc cosine of a number
print("-********************** math.acos()	")
print(math.acos(0.55))
print(math.acos(-0.55))
print(math.acos(0))
print(math.acos(1))
print(math.acos(-1))

# math.acosh()	Returns the inverse hyperbolic cosine of a number
print("-********************** math.acosh()	")
print (math.acosh(7))
print (math.acosh(56))
print (math.acosh(2.45))
print (math.acosh(1))

# math.asin()	Returns the arc sine of a number
print("-********************** math.asin()	")
print(math.asin(0.55))
print(math.asin(-0.55))
print(math.asin(0))
print(math.asin(1))
print(math.asin(-1))


# math.asinh()	Returns the inverse hyperbolic sine of a number
print("-********************** math.asinh()	")
print(math.asinh(7))
print(math.asinh(56))
print(math.asinh(2.45))
print(math.asinh(1))

# math.atan()	Returns the arc tangent of a number in radians
print("-********************** math.atan()	")
print (math.atan(0.39))
print (math.atan(67))
print (math.atan(-21))

# math.atan2()	Returns the arc tangent of y/x in radians
print("-********************** math.atan2()	")
print(math.atan2(8, 5))
print(math.atan2(20, 10))
print(math.atan2(34, -7))

# math.atanh()	Returns the inverse hyperbolic tangent of a number
print("-********************** math.atanh()	")
print(math.atanh(0.59))
print(math.atanh(-0.12))

# math.ceil()	Rounds a number up to the nearest integer
print("-********************** math.ceil()	")
print(math.ceil(1.4))
print(math.ceil(5.3))
print(math.ceil(-5.3))
print(math.ceil(22.6))
print(math.ceil(10.0))

# math.comb()	Returns the number of ways to choose k items from n items without repetition and order
print("-********************** math.comb()	")
# comb giống với tổ hợp trong xác xuất thống kê nCx = n!/(x!*(n-x)!)
# Initialize the number of items to choose from
n = 7
# Initialize the number of possibilities to choose
k = 2
# Print total number of possible combinations
print (math.comb(n, k))

# math.copysign()	Returns a float consisting of the value of the first parameter and the sign of the second parameter
print("-********************** math.copysign()	")
# Trả về giá trị của thông số đầu tiên và dấu của thông số thứ 2
print(math.copysign(4, -1))
print(math.copysign(-8, 97.21))
print(math.copysign(-43, -76))

# math.cos()	Returns the cosine of a number
print("-********************** math.cos()	")
print (math.cos(0.00))
print (math.cos(-1.23))
print (math.cos(10))
print (math.cos(3.14159265359))

# math.cosh()	Returns the hyperbolic cosine of a number
print("-********************** math.cosh()	")
print (math.cosh(1))
print (math.cosh(8.90))
print (math.cosh(0))
print (math.cosh(1.52))

# math.degrees()	Converts an angle from radians to degrees
print("-********************** math.degrees()	")
print (math.degrees(8.90))
print (math.degrees(-20))
print (math.degrees(1))
print (math.degrees(90))

# math.dist()	Returns the Euclidean distance between two points (p and q), where p and q are the coordinates of that point
print("-********************** math.dist()	")
# Tính độ chênh lệch của gốc tọa độ giữa 2 điểm trong hệ tọa độ
p = [3]
q = [1]
# Calculate Euclidean distance
print (math.dist(p, q))
p = [3, 3]
q = [6, 12]
# Calculate Euclidean distance
print (math.dist(p, q))

# math.erf()	Returns the error function of a number
print("-********************** math.erf()	")
# Dùng để trả về một lỗi của số, nhận giá trị từ -inf đến inf và trả lại giá trị từ -1 đến 1, 
print (math.erf(0.67))
print (math.erf(1.34))
print (math.erf(-6))

# math.erfc()	Returns the complementary error function of a number
print("-********************** math.erfc()	")
# Dùng để trả về một hàm lỗi bổ sung của một số, nhận giá trị từ -inf đến inf và trả lại giá trị từ 0 đến 2, 
print (math.erfc(0.67))
print (math.erfc(1.34))
print (math.erfc(-6))

# math.exp()	Returns E raised to the power of x
print("-********************** math.exp()	")
# Dùng để dưa về hàm mũ của một số với cơ số là e^x 
print(math.exp(65))
print(math.exp(-6.89))

# math.expm1()	Returns Ex - 1
print("-********************** math.expm1()	")
print(math.expm1(32))
print(math.expm1(-10.89))

# math.fabs()	Returns the absolute value of a number
print("-********************** math.fabs()	")
# Trả về giá trị tuyệt đối một số nhưng đưa về số thực
print(math.fabs(-66.43))
print(math.fabs(-7))

# math.factorial()	Returns the factorial of a number
print("-********************** factorial()	")
# Trả về giá trị giai thừa của một số ví dụ như 6! = 6*5*4*3*2 = 720
print(math.factorial(9))
print(math.factorial(6))
print(math.factorial(12))

# math.floor()	Rounds a number down to the nearest integer
print("-********************** math.floor()	")
print(math.floor(0.6))
print(math.floor(1.4))
print(math.floor(5.3))
print(math.floor(-5.3))
print(math.floor(22.6))
print(math.floor(10.0))

# math.fmod()	Returns the remainder of x/y
print("-********************** math.fmod()	")
# Trả phép chia lấy dư
print(math.fmod(20, 4))
print(math.fmod(20, 3))
print(math.fmod(15, 6))
print(math.fmod(-10, 3))

# math.frexp()	Returns the mantissa and the exponent, of a specified number
print("-********************** math.frexp()	")
# trả về số dạng (m,e) sao cho number = m * 2**e.
print(math.frexp(4))
print(math.frexp(-4))
print(math.frexp(7))

# math.fsum()	Returns the sum of all items in any iterable (tuples, arrays, lists, etc.)
print("-********************** math.fsum()	")
print(math.fsum([1, 2, 3, 4, 5]))
print(math.fsum([100, 400, 340, 500]))
print(math.fsum([1.7, 0.3, 1.5, 4.5]))

# math.gamma()	Returns the gamma function at x
print("-********************** math.gamma()	")
print(math.gamma(-0.1))
print(math.gamma(8))
print(math.gamma(1.2))
print(math.gamma(80))
print(math.gamma(-0.55))

# math.gcd()	Returns the greatest common divisor of two integers
print("-********************** math.gcd()	")
# Trả về ước số chung của 2 số
print (math.gcd(3, 6))
print (math.gcd(6, 12))
print (math.gcd(12, 36))
print (math.gcd(-12, -36))
print (math.gcd(5, 12))
print (math.gcd(10, 0))
print (math.gcd(0, 34))
print (math.gcd(0, 0))

# math.hypot()	Returns the Euclidean norm
print("-********************** math.hypot()	")
# Trả giá trị như sau sqrt(x*x + y*y). Công thức tổng quát là dạng sqrt(x1*x1 + x2*x2 +x3*x3 .... xn*xn).
parendicular = 3
base = 4
#print the hypotenuse of a right-angled triangle
print(math.hypot(parendicular, base))

# math.isclose()	Checks whether two values are close to each other, or not
print("-********************** math.isclose()	")
# Trả giá trị true hoặc false để xác định việc có giá trị gần nhau của 2 giá trị dựa trên công thức abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol).
print(math.isclose(1.233, 1.4566))
print(math.isclose(1.233, 1.233))
print(math.isclose(1.233, 1.24))
print(math.isclose(1.233, 1.233000001))

# math.isfinite()	Checks whether a number is finite or not
print("-********************** math.isfinite()	")
# Trả giá trị true hoặc false để xác định việc giá trị hữu hạn hay không TRUE là hữu hạn.
print(math.isfinite(2000))
print(math.isfinite(-45.34))
print(math.isfinite(+45.34))
print(math.isfinite(math.inf))
print(math.isfinite(float("nan")))
print(math.isfinite(float("inf")))
print(math.isfinite(float("-inf")))
print(math.isfinite(-math.inf))
print(math.isfinite(0.0))

# math.isinf()	Checks whether a number is infinite or not
print("-********************** math.isinf()	")
# Trả giá trị true hoặc false để xác định việc giá trị hữu hạn hay không TRUE là INF.
print(math.isinf(56))
print(math.isinf(-45.34))
print(math.isinf(+45.34))
print(math.isinf(math.inf))
print(math.isinf(float("nan")))
print(math.isinf(float("inf")))
print(math.isinf(float("-inf")))
print(math.isinf(-math.inf))

# math.isnan()	Checks whether a value is NaN (not a number) or not
print("-********************** math.isnan()	")
print (math.isnan (56))
print (math.isnan (-45.34))
print (math.isnan (+45.34))
print (math.isnan (math.inf))
print (math.isnan (float("nan")))
print (math.isnan (float("inf")))
print (math.isnan (float("-inf")))
print (math.isnan (math.nan))

# math.isqrt()	Rounds a square root number downwards to the nearest integer
print("-********************** math.isqrt()	")
# Print the square root of different numbers
print (math.sqrt(10))
print (math.sqrt (12))
print (math.sqrt (68))
print (math.sqrt (100))
# Round square root downward to the nearest integer
print (math.isqrt(10))
print (math.isqrt (12))
print (math.isqrt (68))
print (math.isqrt (100))

# math.ldexp()	Returns the inverse of math.frexp() which is x * (2**i) of the given numbers x and i
print("-********************** math.ldexp()	")
print(math.ldexp(9, 3))
print(math.ldexp(-5, 2))
print(math.ldexp(15, 2))

# math.lgamma()	Returns the log gamma value of x
print("-********************** math.lgamma()	")
print (math.lgamma(7))
print (math.lgamma(-4.2))

# math.log()	Returns the natural logarithm of a number, or the logarithm of number to base
print("-********************** math.log()	")
print(math.log(2.7183))
print(math.log(2))
print(math.log(1))

# math.log10()	Returns the base-10 logarithm of x
print("-********************** math.log10()	")
print(math.log10(2.7183))
print(math.log10(2))
print(math.log10(1))

# math.log1p()	Returns the natural logarithm of 1+x
print("-********************** math.log1p()	")
print(math.log1p(2.7183))
print(math.log1p(2))
print(math.log1p(1))

# math.log2()	Returns the base-2 logarithm of x
print("-********************** math.log2()	")
print(math.log2(2.7183))
print(math.log2(2))
print(math.log2(1))

# math.perm()	Returns the number of ways to choose k items from n items with order and without repetition
print("-********************** math.perm()	")
# Đây giống với chỉnh hợp , số lần lấy ra vật mà không lặp lại, nếu không có thông số k thì mặc định là tính giai thùa
# Initialize the number of items to choose from
n = 7
# Initialize the number of items to choose
k = 4
# Print the number of ways to choose k items from n items
print (math.perm(n, k))

# math.pow()	Returns the value of x to the power of y
print("-********************** math.pow()	")
print(math.pow(9, 3))

# math.prod()	Returns the product of all the elements in an iterable
print("-********************** math.prod()	")
# Tính giá trị bằng cách nhân toàn bộ các giá trị được đưa vào
sequence = (2, 2, 2)
#Return the product of the elements
print(math.prod(sequence))

# math.radians()	Converts a degree value into radians
print("-********************** math.radians()	")
print(math.radians(180))
print(math.radians(100.03))
print(math.radians(-20))

# math.remainder()	Returns the closest value that can make numerator completely divisible by the denominator
print("-********************** math.remainder()	")
# Lấy giá trị gần nhất sao cho tử số - x  có thể chia hết cho mẫu số , dạng a/b thì a là tử số, b là mẫu số (a -x ) mod b = 0
print (math.remainder(9, 2))
print (math.remainder(9, 3))
print (math.remainder(18, 4))

# math.sin()	Returns the sine of a number
print("-********************** math.sin()	")
print (math.sin(0.00))
print (math.sin(-1.23))
print (math.sin(10))
print (math.sin(math.pi))
print (math.sin(math.pi/2))

# math.sinh()	Returns the hyperbolic sine of a number
print("-********************** math.sinh()	")
print(math.sinh(0.00))
print(math.sinh(-23.45))
print(math.sinh(23))
print(math.sinh(1.00))
print(math.sinh(math.pi))

# math.sqrt()	Returns the square root of a number
print("-********************** math.sqrt()	")
print (math.sqrt(9))
print (math.sqrt(25))
print (math.sqrt(16))

# math.tan()	Returns the tangent of a number
print("-********************** math.tan()	")
print (math.tan(90))
print (math.tan(-90))
print (math.tan(45))
print (math.tan(60))

# math.tanh()	Returns the hyperbolic tangent of a number
print("-**********************math.tanh()	")
print(math.tanh(8))
print(math.tanh(1))
print(math.tanh(-6.2))

# math.trunc()	Returns the truncated integer parts of a number
print("-**********************math.trunc()	")
# Chỉ lấy phần nguyên của một số
print(math.trunc(2.77))
print(math.trunc(8.32))
print(math.trunc(-99.29))

# math.e	Returns Euler's number (2.7182...)
print("-**********************math.e	")
print (math.e)

# math.inf	Returns a floating-point positive infinity
print("-**********************math.inf	")
print (math.inf)

# math.nan	Returns a floating-point NaN (Not a Number) value
print("-**********************math.nan	")
print (math.nan)

# math.pi	Returns PI (3.1415...)
print("-********************** math.pi	")
print (math.pi)

# math.tau	Returns tau (6.2831...)
print("-********************** math.tau	")
print (math.tau)