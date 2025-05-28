from django.db import models

# Create your models here.
class Blogs(models.Model):
    Image=models.ImageField(null=True,blank=True) # Tạo trường image cho khả năng null và blank
    title=models.CharField(max_length=200,null=True) #Tạo title có tối đa 200 ký tự
    description=models.CharField(max_length=1200,null=True)
    date=models.DateField(auto_now_add=True,null=True) #Tạo trường date nhưng có tự động điền ngày hiện tại #Nếu True thì mặc định không hiện khi kế thừa trong form
    likes=models.IntegerField(default=0) # Tạo trường like với số lượt like mặc định là 0