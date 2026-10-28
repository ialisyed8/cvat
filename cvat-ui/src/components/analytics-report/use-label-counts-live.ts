// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import { useEffect, useState } from 'react';

import { LabelCounts, getCore } from 'cvat-core-wrapper';

const core = getCore();

const MIN_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;
// the server closes with 4000 + HTTP status; reconnecting does not help with these
const FINAL_CLOSE_CODES = [4400, 4401, 4403, 4404];

export enum LiveStatus {
    CONNECTING = 'connecting',
    LIVE = 'live',
    RECONNECTING = 'reconnecting',
    STOPPED = 'stopped',
}

interface SerializedLabelCounts {
    task_id: number;
    group_by: LabelCounts['groupBy'];
    total: number;
    results: { label: string; shape_type?: LabelCounts['results'][0]['shapeType']; count: number }[];
}

function labelCountsSocketURL(taskId: number, groupBy: LabelCounts['groupBy']): string {
    const url = new URL(
        `${core.config.backendAPI}/annotation-analytics/tasks/${taskId}/label-counts/ws`,
        window.location.href,
    );
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    if (groupBy) {
        url.searchParams.set('group_by', groupBy);
    }
    return url.toString();
}

export function useLabelCountsLive(
    taskId: number,
    groupBy: LabelCounts['groupBy'],
    enabled: boolean,
    onUpdate: (labelCounts: LabelCounts) => void,
): LiveStatus {
    const [status, setStatus] = useState(LiveStatus.CONNECTING);

    useEffect(() => {
        if (!enabled) {
            return () => {};
        }

        let socket: WebSocket | null = null;
        let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
        let reconnectDelay = MIN_RECONNECT_DELAY_MS;
        let disposed = false;

        const connect = (): void => {
            socket = new WebSocket(labelCountsSocketURL(taskId, groupBy));
            socket.onmessage = (event: MessageEvent<string>) => {
                const data: SerializedLabelCounts = JSON.parse(event.data);
                reconnectDelay = MIN_RECONNECT_DELAY_MS;
                setStatus(LiveStatus.LIVE);
                onUpdate({
                    taskId: data.task_id,
                    groupBy: data.group_by,
                    total: data.total,
                    results: data.results.map(({ label, shape_type: shapeType, count }) => ({
                        label, shapeType, count,
                    })),
                });
            };
            socket.onclose = (event: CloseEvent) => {
                if (disposed) {
                    return;
                }

                if (FINAL_CLOSE_CODES.includes(event.code)) {
                    setStatus(LiveStatus.STOPPED);
                    return;
                }

                setStatus(LiveStatus.RECONNECTING);
                reconnectTimeout = setTimeout(connect, reconnectDelay);
                reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY_MS);
            };
        };

        setStatus(LiveStatus.CONNECTING);
        connect();

        return () => {
            disposed = true;
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
            }
            socket?.close();
        };
    }, [taskId, groupBy, enabled, onUpdate]);

    return status;
}
