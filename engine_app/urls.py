from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.admin, name='admin'),
    path('login/', views.user_login, name='user_login'),
    #path('login/', views.user_logout, name='user_logout'),
    path('',views.home, name='home'),
    path('import_file/', views.import_files, name='import_f'),
    path('import_mt/', views.import_mapping_table, name='import_mt'),
    path('brows_mapping_table/', views.brows_mapping_table, name='brows_mapping_t'),
    path('mapping_rules/', views.brows_define_mrules, name='brows_d_mrules'),
    path('mapping_sets/', views.brows_define_msets, name='brows_d_msets'),
    path('master_data/', views.master_data, name='master_data'),
    path('import_master_d/', views.import_master_d, name='import_master_d'),
    path('brows_master_t/', views.brows_master_t, name='brows_master_t'),
    path('define_master_t/', views.define_master_t, name='define_master_t'),
    path('define_mt/', views.define_mapping_table, name='define_mt'),
    path('export/', views.export_data, name='export_data'),
    path('mapping_data/', views.mapping_data, name='mapping_data'),
    path('perform_data/', views.perform_the_data, name='perform_data'),
    ]