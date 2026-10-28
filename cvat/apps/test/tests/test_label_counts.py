# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from django.contrib.auth.models import Group
from rest_framework import status

from cvat.apps.engine.models import Job, LabeledShape
from cvat.apps.engine.tests.test_rest_api import create_db_task
from cvat.apps.engine.tests.utils import ApiTestBase
from cvat.apps.iam.models import User


class LabelCountsTest(ApiTestBase):
    @classmethod
    def setUpTestData(cls):
        user_group, _ = Group.objects.get_or_create(name="user")
        cls.admin = User.objects.create_superuser(username="admin", email="", password="admin")
        cls.owner = User.objects.create_user(username="owner", password="owner")
        cls.owner.groups.set([user_group])
        cls.outsider = User.objects.create_user(username="outsider", password="outsider")
        cls.outsider.groups.set([user_group])

        cls.task = create_db_task(
            {
                "name": "label counts",
                "owner": cls.owner,
                "overlap": 0,
                "segment_size": 2,
                "image_quality": 75,
                "size": 4,
                "labels": [{"name": "car"}, {"name": "person"}, {"name": "dog"}],
            }
        )
        labels = {label.name: label for label in cls.task.label_set.all()}
        jobs = list(Job.objects.filter(segment__task=cls.task).order_by("segment__start_frame"))
        assert len(jobs) == 2

        def add_shape(job, label, shape_type, **kwargs):
            return LabeledShape.objects.create(
                job=job,
                label=labels[label],
                frame=job.segment.start_frame,
                type=shape_type,
                points=[0, 0, 1, 1],
                **kwargs,
            )

        add_shape(jobs[0], "person", "rectangle")
        add_shape(jobs[1], "person", "rectangle")
        add_shape(jobs[0], "car", "polygon")
        parent = add_shape(jobs[1], "car", "mask")
        # an element of another shape must not be counted on its own
        add_shape(jobs[1], "car", "points", parent=parent)

    def _url(self, task_id):
        return f"/api/annotation-analytics/tasks/{task_id}/label-counts"

    def test_requires_login(self):
        response = self.client.get(self._url(self.task.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refuses_user_without_task_access(self):
        response = self._get_request(self._url(self.task.id), self.outsider)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_task(self):
        response = self._get_request(self._url(self.task.id + 1000), self.admin)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_counts_per_label_across_jobs(self):
        for user in (self.admin, self.owner):
            with self.subTest(user=user.username):
                response = self._get_request(self._url(self.task.id), user)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(
                    response.json(),
                    {
                        "task_id": self.task.id,
                        "group_by": None,
                        "total": 4,
                        "results": [
                            {"label": "car", "count": 2},
                            {"label": "person", "count": 2},
                        ],
                    },
                )

    def test_group_by_shape_type(self):
        response = self._get_request(
            self._url(self.task.id), self.admin, query_params={"group_by": "shape_type"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["results"],
            [
                {"label": "person", "shape_type": "rectangle", "count": 2},
                {"label": "car", "shape_type": "mask", "count": 1},
                {"label": "car", "shape_type": "polygon", "count": 1},
            ],
        )

    def test_rejects_unknown_grouping(self):
        response = self._get_request(
            self._url(self.task.id), self.admin, query_params={"group_by": "color"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
