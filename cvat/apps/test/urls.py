# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from rest_framework import routers

from cvat.apps.test import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(
    "annotation-analytics/tasks", views.AnnotationAnalyticsViewSet, basename="annotation_analytics"
)

urlpatterns = router.urls
