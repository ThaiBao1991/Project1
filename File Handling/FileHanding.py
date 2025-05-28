# -****************************** File Handing
print("-********************** File Handing")
f = open("demofile.txt", "r")
print(f.read())

# -Open a File on the Server
print("-Open a File on the Server")
f = open("demofile.txt", "r")
print(f.read())

print("-Open a File on the Server with Path ")
f = open("C:\\Users\\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\demofile.txt", "r")
print(f.read())

# - Read Only Parts of the File
print("-Read Only Parts of the File")
f = open("demofile.txt", "r")
print(f.read(5))

# - Read Lines
print("-Read Lines")
f = open("demofile.txt", "r")
print(f.readline())

f = open("demofile.txt", "r")
print(f.readline())
print(f.readline())

f = open("demofile.txt", "r")
for x in f:
  print(x)

# - Close Files
print("-Close Files")
f = open("demofile.txt", "r")
print(f.readline())
f.close()

# ******************************** Python Write / Create Files
print("************************ Python Write")
# Sử dụng lệnh a thì sẽ chèn thêm nội dung vào file
f = open("demofile.txt", "a")
f.write("Now the file has more content!")
f.close()
#open and read the file after the appending:
f = open("demofile.txt", "r")
print(f.read())

# Sử dung w sẽ viết lại file theo kiểu lưu chồng nội dung
f = open("demofile.txt", "w")
f.write("Woops! I have deleted the content!")
f.close()
#open and read the file after the overwriting:
f = open("demofile.txt", "r")
print(f.read())

# Create a New File
print("************************ Create a New File")
# với lệnh x sẽ báo lỗi nếu file đã được tạo
# f = open("myfile1.txt", "x")
# Create a new file if it does not exist:
f = open("myfile1.txt", "w")
f.close()

# ******************************** Delete File
print("************************ Delete File")
import os
os.remove("myfile1.txt")

# -Check if File exist:
print("- Check if File exist")
if os.path.exists("myfile1.txt"):
  os.remove("myfile1.txt")
else:
  print("The file does not exist")

# -Delete Folder
print("- Delete Folder")
# Lưu ý lệnh rmdir chỉ có thể xóa folder rỗng
os.mkdir("myfolder")
os.rmdir("myfolder")
