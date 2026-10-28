# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from cvat.apps.engine.permissions import TaskPermission


class AnnotationAnalyticsPermission(TaskPermission):
    """
    Maps the analytics actions to existing task scopes,
    so access is decided by the task OPA rules without new rules.
    """

    @classmethod
    def _get_scopes(cls, request, view, obj):
        return [
            {
                ("label_counts", "GET"): cls.Scopes.VIEW_ANNOTATIONS,
            }[(view.action, request.method)]
        ]
