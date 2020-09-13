#!/bin/bash

rm ~/.tagit/tagit.db

tagit record figure "color=red, shape=sphere, weight=10kg" -- "echo nr_edges: 0 && echo nr_vertices: 0 && echo density: 10kg/m3" > /dev/null
tagit record figure "color=yellow, shape=cube, weight=10kg" -- "echo nr_edges: 12 && echo nr_vertices: 8 && echo density: 20kg/m3" > /dev/null
tagit record figure "color=green, shape=tetrahedron, weight=5kg" -- "echo nr_edges: 6 && echo nr_vertices: 4 && echo density: 10kg/m3" > /dev/null
tagit parse add figure nr_edges "awk '/^nr_edges/{print \$NF}'" > /dev/null
tagit parse add figure nr_vertices "awk '/^nr_vertices/{print \$NF}'" > /dev/null
tagit parse add figure -s nr_vertices result "cat | sed 's/^/nr_vertices: /'" > /dev/null
tagit parse add figure -s nr_edges result "cat | sed 's/^/nr_edges: /'" > /dev/null

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=16GB" -- "echo IOPS: 40K && echo latency: 10us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=32GB" -- "echo IOPS: 60K && echo latency: 10us" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null

# 1. List exps
printf "Basic test.. "

list=$(tagit list)
list_gt=$'figure
perf'

if [ "$list_gt" != "$list" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 2. List tags and data categories
printf "per-exp test.. "

list=$(tagit list figure)
list_gt=$'[figure] List of tags:
- color
- shape
- weight
[figure] List of data categories:
- raw
- nr_edges
- nr_vertices
- result'

if [ "$list_gt" != "$list" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

echo "Test passed"
