from django.contrib import admin
from django.contrib.auth.models import Group
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 设置标题
admin.site.site_header = '南开大学团委学生服务系统'
admin.site.site_title = '南开大学团委学生服务系统'
admin.site.index_title = '后台管理'

# 注销Django自带的用户组
admin.site.unregister(Group)
