from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.contrib.auth.views import login, logout

urlpatterns = patterns('app.views',
    # Examples:
    # url(r'^$', 'Trabajo.views.home', name='home'),
    # url(r'^Trabajo/', include('Trabajo.foo.urls')),
    url(r'^home/$','home'),
    url(r'^$','home'),
    url(r'^login/nuevo$','nuevo_usuario'),
    url(r'^login/$','login'),
    url(r'^logout/$','logout'),
    url(r'^noticias/$','noticias'),
    url(r'^perfil/$','profile'),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
