from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from myapp import views
from myapp.views import qna,post_review


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.weather, name='weather'),
    path('trend/', views.trend, name='trend'),
    path('method_of_use/', views.method_of_use, name='method_of_use'),
    path('situation/', views.situation, name='situation'),
    path('season/', views.season, name='season'),
    path('qna/', views.qna, name='qna'),
    path('post_review/', views.post_review, name='post_review'),
    path('delete_review/<int:review_id>/', views.delete_review, name='delete_review'),
]




if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
