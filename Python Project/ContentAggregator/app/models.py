from django.db import models
 
# Create your models here.
class PyContent(models.Model): #Tạo model PyContent => Table PyContent trong database
  headline = models.CharField(max_length=300) #Trường headline có dang là char với số ký tự tối đa là 300
  img = models.URLField(null=True, blank=True) #Tạo trường img dạng url có khả năng trống và dạng ""
  url = models.TextField()  #Tạo trường url có dạng là textfield
  def __str__(self): #định nghĩa hàm str nếu gọi thì sẽ hiện ra headline giống hàm ToString trong java
    return self.headline
 
class ProgContent(models.Model):
  headline = models.CharField(max_length=300)
  img = models.URLField(null=True, blank=True)
  url = models.TextField()
  def __str__(self):
    return self.headline
 
class HiringContent(models.Model):
  headline = models.CharField(max_length=300)
  img = models.URLField(null=True, blank=True)
  url = models.TextField()
  def __str__(self):
    return self.headline
 
class CovidContent(models.Model):
  headline = models.CharField(max_length=300)
  img = models.URLField(null=True, blank=True)
  url = models.TextField()
  def __str__(self):
    return self.headline