"""idp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, patterns, include
from django.contrib.auth.models import User, Group
from django.contrib import admin

admin.autodiscover()
import permission; permission.autodiscover()

from rest_framework import permissions, routers, serializers, viewsets


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group



# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^admin/', admin.site.urls),
]
