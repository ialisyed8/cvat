# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from django.db.models import Count, F
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cvat.apps.engine.models import LabeledShape, Task
from cvat.apps.engine.types import ExtendedRequest
from cvat.apps.test.permissions import AnnotationAnalyticsPermission
from cvat.apps.test.serializers import LabelCountsSerializer


class AnnotationAnalyticsViewSet(viewsets.GenericViewSet):
    queryset = Task.objects.select_related("organization")
    iam_permission_class = AnnotationAnalyticsPermission
    iam_supports_organization_params = False

    @extend_schema(
        summary="Get the number of annotations per label in a task",
        description=(
            "Counts top-level shapes (LabeledShape) in all jobs of the task. "
            "Tracks, tags and skeleton elements are not included."
        ),
        responses={"200": LabelCountsSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="label-counts", filter_backends=[])
    def label_counts(self, request: ExtendedRequest, pk: int):
        task = self.get_object()  # call check_object_permissions as well

        rows = (
            LabeledShape.objects.filter(job__segment__task_id=task.id, parent__isnull=True)
            .values(label_name=F("label__name"))
            .annotate(count=Count("id"))
            .order_by("-count", "label_name")
        )
        results = list(rows)

        serializer = LabelCountsSerializer(
            {
                "task_id": task.id,
                "total": sum(row["count"] for row in results),
                "results": results,
            }
        )
        return Response(serializer.data)
