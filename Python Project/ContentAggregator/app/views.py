from app.models import *
from django.shortcuts import render,redirect
from django.http  import HttpResponse
import feedparser
 
# Create your views here.
def updatepython(request):
    #-------python----------------
    PyContent.objects.all().delete() # xóa toàn bộ dữ liệu trong table PyContent
    url = feedparser.parse(
            "https://medium0.com/feed/tag/python"
        )
    # print(url) # Lấy dữ liệu của url
    data = url.entries
    # print(data)
    numberCourse = len(data)
    # print (numberCourse)
    if numberCourse >10 :
        numberCourse =10
    else:
        print("Số lượng nhỏ hơn 10")
    # print (info[0])
    
    for i in range(numberCourse):
        info = data[i]
        content= PyContent()
        content.headline= info.title
        print("################################")
        print(content.headline)
        #-----finding image link
        desc = info.description
        start=desc.find("img src=")
        end=desc.find("width")
        
        print(desc[end:])
        desc=desc[start+9:end-2:]
        print("-----------------------------")
        print(desc)
 
        #---------------
        content.img = desc
        content.url  = info.link
        content.save()
    
    return redirect('/')
 
def updatecovid(request):
    #-------python----------------
    covidcontent = CovidContent.objects.all().delete()
    url = feedparser.parse(
            "https://medium0.com/feed/tag/covid"
        )
    data = url.entries
    numberCourse = len(data)
    # print (numberCourse)
    if numberCourse >10 :
        numberCourse =10
    else:
        print("Số lượng nhỏ hơn 10")
    for i in range(numberCourse -1):
        info = data[i]
        content= CovidContent()
        content.headline= info.title
        print("################################")
        print(content.headline)
        #-----finding image link
        desc = info.description
        start=desc.find("img src=")
        end=desc.find("width")
        
        print(desc[end:])
        desc=desc[start+9:end-2:]
        print("-----------------------------")
        print(desc)
 
        #---------------
        content.img = desc
        content.url  = info.link
        content.save()
    
    return redirect('/')
 
def updateprog(request):
    #-------python----------------
    progcontent = ProgContent.objects.all().delete()
    url = feedparser.parse(
            "https://medium0.com/feed/tag/programming"
        )
    data = url.entries
    numberCourse = len(data)
    # print (numberCourse)
    if numberCourse >10 :
        numberCourse =10
    else:
        print("Số lượng nhỏ hơn 10")
    for i in range(numberCourse -1):
        info = data[i]
        content= ProgContent()
        content.headline= info.title
        #-----finding image link
        desc = info.description
        start=desc.find("img src=")
        end=desc.find("width")
        
        print(desc[end:])
        desc=desc[start+9:end-2:]
        print("-----------------------------")
        print(desc)
 
        #---------------
        content.img = desc
        content.url  = info.link
        content.save()
    
    return redirect('/')
 
def updatehiring(request):
    #-------python----------------
    hiringcontent = HiringContent.objects.all().delete()
    url = feedparser.parse(
            "https://medium0.com/feed/tag/hiring"
        )
    data = url.entries
    numberCourse = len(data)
    # print (numberCourse)
    if numberCourse >10 :
        numberCourse =10
    else:
        print("Số lượng nhỏ hơn 10")
    for i in range(numberCourse -1 ):
        info = data[i]
        content= HiringContent()
        content.headline= info.title
        #-----finding image link
        desc = info.description
        start=desc.find("img src=")
        end=desc.find("width")
        
        print(desc[end:])
        desc=desc[start+9:end-2:]
        print("-----------------------------")
        print(desc)
 
        #---------------
        content.img = desc
        content.url  = info.link
        content.save()
    
    return redirect('/')
 
def home(request):
    pycontent = PyContent.objects.all()
    progcontent = ProgContent.objects.all()
    hiringcontent = HiringContent.objects.all()
    covidcontent = CovidContent.objects.all()
    context = { 
        'pycontent': pycontent,
        'progcontent': progcontent,
        'hiringcontent': hiringcontent,
        'covidcontent': covidcontent,
    }
    return render(request,'app/home.html',context)