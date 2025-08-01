"""
URL configuration for project_run project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from autos.artem_debug import UploadFileView
from autos.views import get_autos, get_company_details, PositionViewSet, UsersViewSet, \
    subscribe_to_coach_api_url, ChallengeViewSet, get_challenges_summary, rate_coach, analytics_for_coach, \
    UploadXLSX, CollectableItemViewSet, get_challenges, AthleteInfoViewSet, RunsViewSet, AnalyticsForCoachAPIView

router = DefaultRouter()
router.register(r'users', UsersViewSet)
router.register(r'runs', RunsViewSet)
router.register(r'positions', PositionViewSet)
router.register(r'challenges', ChallengeViewSet)
router.register(r'athlete_info', AthleteInfoViewSet)
router.register(r'collectible_item', CollectableItemViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('autos/', get_autos, name='autos'),
    path('api/subscribe_to_coach/<int:id>/', subscribe_to_coach_api_url, name='subscribe_to_coach'),
    path('api/company_details/', get_company_details, name='company_details'),
    path('api/challenges_summary/', get_challenges_summary, name='challenges_summary'),
    # path('api/challenges/', get_challenges, name='challenges_summary'),
    path('api/rate_coach/<int:coach_id>/', rate_coach, name='rate_coach'),
    path('api/analytics_for_coach/<int:coach_id>/', AnalyticsForCoachAPIView.as_view()),
    # path('api/analytics_for_coach/<int:coach_id>/', analytics_for_coach, name='analytics_for_coach'),
    # path('api/upload_file/', UploadXLSX.as_view(), name='unit_location_upload'),
    path('api/upload_file/', UploadFileView.as_view(), name='unit_location_upload'),

    path('api/', include(router.urls))
]

# Add Django Debug Toolbar URLs when in debug mode
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
# test2