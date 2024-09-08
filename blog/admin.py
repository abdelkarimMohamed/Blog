from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    
    list_display=['title','slug','author','publish','status']
    list_filter=['status','publish','created','author']
    search_fields=['title','body']
    prepopulated_fields={'slug':('title',)} # slug created authomatic when type title
    raw_id_fields=['author'] # write id author in field author
    date_hierarchy='publish'  #  filter by publish => Their location above
    ordering=['status','publish']