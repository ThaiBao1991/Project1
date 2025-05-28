from django.contrib import admin

# Register your models here.
from .models import Post, Comment

# Register your models here.
class CommentInline(admin.StackedInline):
    model = Comment

class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'date']
    list_filter = ['date']
    search_fields = ['title']
    inlines = [CommentInline]
 
admin.site.register(Post, PostAdmin)

#Sử dụng TabularInline
# from django.contrib import admin

# # Register your models here.
# from .models import Post, Comment

# # Register your models here.
# class CommentInline(admin.TabularInline):
#     model = Comment

# class PostAdmin(admin.ModelAdmin):
#     list_display = ['title', 'date']
#     list_filter = ['date']
#     search_fields = ['title']
#     inlines = [CommentInline]
 
# admin.site.register(Post, PostAdmin)