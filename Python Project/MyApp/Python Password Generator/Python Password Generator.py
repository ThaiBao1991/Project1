#importing required libraries for TechVidvan Password Generator project using Python
import random
from tkinter import *
import tkinter

window = Tk()
window.title('Password Generator By TB') # Đặt tiêu đề cho app
window.geometry('500x500') # Cài đặt kích thước cho app

Label(window,font=('bold',10),text='PASSWORD GENERATOR').pack()
l = Label(window,text ="",font=('bold', 30)) #Gán biến l cho giá trị Label được tạo
l.place(x=180,y=50) # Đặt vị trí của label l trong window
len=tkinter.IntVar() # Đặt biến len nhận giá trị là integer

def password_generate(leng): #Tạo hàm để random giá trị
    valid_char='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@_' # List các giá trị ký tự có thể gán
    password=''.join(random.sample(valid_char,leng)) #tạo password từ các giá trị random trên
    l.config(text="") #set label l về chuỗi rỗng
    l.config(text = password)  #set giá trị text của l = password được tạo ra ở trên

def clearText(): # Tạo hàm mục đích để reset giá trị text của l về rỗng
    l.config(text="") #Set gia trị của label l về rỗng

def get_len(): #Hàm lựa chọn quyết định lựa chọn khi len =4,6, 8
    if len.get() == 4:
        password_generate(4)
    elif len.get() == 6:
        password_generate(6)
    elif len.get() == 8:
        password_generate(8)
    else:
        password_generate(6)    

Button(window,text='Generate',font=('normal',10), bg='yellow',command=get_len).place(x=200,y=110) # Thêm button vào mục đích chạy get_len
Button(window,text='ClearText',font=('normal',10), bg='red',command=clearText).place(x=200,y=140) # Thêm button vào mục đích chạy clearText
Checkbutton(text='4 character',onvalue=4, offvalue=0,variable=len).place(x=200,y=170) #Thêm vào Checkbutton vào vị trí x=200, y= 170, với tọa độ gốc tại vị trí trên cùng góc trái
Checkbutton(text='6 character',onvalue=6, offvalue=0,variable=len).place(x=200,y=190)
Checkbutton(text='8 character',onvalue=8, offvalue=0,variable=len).place(x=200,y=210)

window.mainloop()