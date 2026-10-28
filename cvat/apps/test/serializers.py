# Copyright (C) CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

from rest_framework import serializers


class LabelCountsQuerySerializer(serializers.Serializer):
    group_by = serializers.ChoiceField(choices=["shape_type"], required=False)


class LabelCountSerializer(serializers.Serializer):
    label = serializers.CharField(source="label_name")
    shape_type = serializers.CharField(source="type", required=False)
    count = serializers.IntegerField()


class LabelCountsSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    group_by = serializers.CharField(allow_null=True)
    total = serializers.IntegerField()
    results = LabelCountSerializer(many=True)
