# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from rest_framework import serializers


class LabelCountSerializer(serializers.Serializer):
    label = serializers.CharField(source="label_name")
    count = serializers.IntegerField()


class LabelCountsSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    total = serializers.IntegerField()
    results = LabelCountSerializer(many=True)
