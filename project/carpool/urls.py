from django.urls import path
from carpool import views
from carpool.models import Carpools

# index_list_view = views.IndexListView.as_view(
#     queryset=Carpools.objects.order_by('carpool_id'),
#     context_object_name = 'carpool_list',
#     template_name='carpool/carpool_info.html'
# )

urlpatterns = [
    path('', views.home, name='home'),
    path('index/', views.index, name= 'index' ),
    # path('index/', index_list_view, name= 'index' ),
    path('<int:carpool_id>/', views.details, name= 'details'),
    path('upload/', views.upload, name='upload'),
    path('about/', views.about, name='about'),
    path('csv_file/', views.generate_csv_file, name='csv_file'),
]

