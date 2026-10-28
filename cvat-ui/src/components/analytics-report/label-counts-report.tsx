// Copyright (C) CVAT.ai Corporation
//
// SPDX-License-Identifier: MIT

import React, { useCallback, useEffect, useState } from 'react';
import Button from 'antd/lib/button';
import Card from 'antd/lib/card';
import Empty from 'antd/lib/empty';
import Radio from 'antd/lib/radio';
import Result from 'antd/lib/result';
import Space from 'antd/lib/space';
import Tag from 'antd/lib/tag';
import Text from 'antd/lib/typography/Text';

import { LabelCounts, getCore } from 'cvat-core-wrapper';
import CVATLoadingSpinner from 'components/common/loading-spinner';
import { LiveStatus, useLabelCountsLive } from './use-label-counts-live';

const core = getCore();

const ROW_HEIGHT = 24;
const LABEL_WIDTH = 200;
const BAR_AREA_WIDTH = 480;
const COUNT_WIDTH = 60;
const CHART_WIDTH = LABEL_WIDTH + BAR_AREA_WIDTH + COUNT_WIDTH;

type GroupBy = 'label' | 'shape_type';

const LIVE_STATUS_TAGS: Record<LiveStatus, { color: string; text: string }> = {
    [LiveStatus.CONNECTING]: { color: 'default', text: 'Connecting to live updates' },
    [LiveStatus.LIVE]: { color: 'success', text: 'Live' },
    [LiveStatus.RECONNECTING]: { color: 'warning', text: 'Reconnecting' },
    [LiveStatus.STOPPED]: { color: 'default', text: 'Live updates stopped' },
};

interface ChartProps {
    labelCounts: LabelCounts;
}

function LabelCountsChart(props: Readonly<ChartProps>): JSX.Element {
    const { labelCounts: { results } } = props;
    const maxCount = Math.max(...results.map((row) => row.count));

    return (
        <svg
            className='cvat-label-counts-chart'
            viewBox={`0 0 ${CHART_WIDTH} ${results.length * ROW_HEIGHT}`}
            role='img'
            aria-label='Number of annotations per label'
        >
            {results.map((row, index) => {
                const name = row.shapeType ? `${row.label} (${row.shapeType})` : row.label;
                const barWidth = Math.max(1, (row.count / maxCount) * BAR_AREA_WIDTH);
                return (
                    <g key={name} transform={`translate(0, ${index * ROW_HEIGHT})`}>
                        <title>{`${name}: ${row.count}`}</title>
                        <text
                            className='cvat-label-counts-chart-label'
                            x={LABEL_WIDTH - 8}
                            y={ROW_HEIGHT / 2}
                            textAnchor='end'
                            dominantBaseline='middle'
                        >
                            {name}
                        </text>
                        <rect
                            className='cvat-label-counts-chart-bar'
                            x={LABEL_WIDTH}
                            y={4}
                            width={barWidth}
                            height={ROW_HEIGHT - 8}
                        />
                        <text
                            className='cvat-label-counts-chart-count'
                            x={LABEL_WIDTH + barWidth + 6}
                            y={ROW_HEIGHT / 2}
                            dominantBaseline='middle'
                        >
                            {row.count}
                        </text>
                    </g>
                );
            })}
        </svg>
    );
}

interface Props {
    taskId: number;
}

function LabelCountsReport(props: Readonly<Props>): JSX.Element {
    const { taskId } = props;
    const [groupBy, setGroupBy] = useState<GroupBy>('label');
    const [labelCounts, setLabelCounts] = useState<LabelCounts | null>(null);
    const [error, setError] = useState<Error | null>(null);
    const [fetching, setFetching] = useState(true);

    const fetchLabelCounts = useCallback(async (): Promise<void> => {
        setFetching(true);
        setError(null);
        try {
            const filter = groupBy === 'shape_type' ? { groupBy } : {};
            setLabelCounts(await core.analytics.labelCounts(taskId, filter));
        } catch (fetchError: unknown) {
            setLabelCounts(null);
            setError(fetchError instanceof Error ? fetchError : new Error(String(fetchError)));
        } finally {
            setFetching(false);
        }
    }, [taskId, groupBy]);

    useEffect(() => {
        fetchLabelCounts();
    }, [fetchLabelCounts]);

    const liveStatus = useLabelCountsLive(
        taskId,
        groupBy === 'shape_type' ? groupBy : null,
        !fetching && !error,
        setLabelCounts,
    );

    let content: JSX.Element | null = null;
    if (fetching) {
        content = <CVATLoadingSpinner />;
    } else if (error) {
        content = (
            <Result
                className='cvat-label-counts-error'
                status='error'
                title='Could not load annotation counts'
                subTitle={error.message}
                extra={<Button type='primary' onClick={fetchLabelCounts}>Retry</Button>}
            />
        );
    } else if (labelCounts && labelCounts.total === 0) {
        content = <Empty className='cvat-label-counts-empty' description='No annotations yet' />;
    } else if (labelCounts) {
        content = (
            <>
                <Text type='secondary'>{`Total: ${labelCounts.total} shapes (tracks and tags are not counted)`}</Text>
                <LabelCountsChart labelCounts={labelCounts} />
            </>
        );
    }

    return (
        <Card
            className='cvat-label-counts-report'
            title='Annotations per label'
            extra={(
                <Space>
                    {!fetching && !error && (
                        <Tag className='cvat-label-counts-live-status' color={LIVE_STATUS_TAGS[liveStatus].color}>
                            {LIVE_STATUS_TAGS[liveStatus].text}
                        </Tag>
                    )}
                    <Radio.Group
                        value={groupBy}
                        disabled={fetching}
                        onChange={(event) => setGroupBy(event.target.value)}
                        optionType='button'
                        options={[
                            { label: 'By label', value: 'label' },
                            { label: 'By label and shape type', value: 'shape_type' },
                        ]}
                    />
                </Space>
            )}
        >
            {content}
        </Card>
    );
}

export default React.memo(LabelCountsReport);
