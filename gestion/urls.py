from django.urls import path
from . import views, relaciones_crud

app_name = 'gestion'
urlpatterns = [
    path('', views.InicioView.as_view(), name='inicio'),
    path('tablas/<slug:slug>/', views.ListadoView.as_view(), name='listado'),
    path('tablas/<slug:slug>/nuevo/', views.CrearView.as_view(), name='crear'),
    path('tablas/<slug:slug>/<str:pk>/', views.DetalleView.as_view(), name='detalle'),
    path('tablas/<slug:slug>/<str:pk>/editar/', views.EditarView.as_view(), name='editar'),
    path('tablas/<slug:slug>/<str:pk>/eliminar/', views.EliminarView.as_view(), name='eliminar'),
    path('relaciones/<slug:slug>/', views.RelacionesView.as_view(), name='relaciones'),
    path('relaciones/<slug:slug>/nuevo/', relaciones_crud.nueva_relacion, name='nueva_relacion'),
    path('relaciones/<slug:slug>/<str:pk1>/<str:pk2>/editar/', relaciones_crud.editar_relacion, name='editar_relacion'),
    path('relaciones/<slug:slug>/<str:pk1>/<str:pk2>/eliminar/', relaciones_crud.eliminar_relacion, name='eliminar_relacion'),
]
