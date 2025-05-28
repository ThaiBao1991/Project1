from django.forms import ModelForm
from .models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
 
class createuserform(UserCreationForm): # Lấy từ form uer mặc định có sẵn
    class Meta:
        model=User
        fields=['username']  # Mặc định sẽ thêm vào password và Password Confirmation
        # fields=['username','password'] 
        # fields='__all__'
 
class createcustomerform(ModelForm): 
    class Meta: # Thừa hưởng từ Model khác
        model=Customer # Lấy các trường của Customer làm dữ liệu cần nhập
        fields='__all__' # Lấy toàn bộ trường
        exclude=['user'] # Trừ trường user ra
 
class createbookform(ModelForm):
    class Meta: 
        model=Book
        fields='__all__' 