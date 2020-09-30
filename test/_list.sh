#!/bin/bash

rm ~/.tagit/tagit.db

printf "nr_edges: 0\nnr_vertices: 0\ndensity: 10kg/m3" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
printf "nr_edges: 12\nnr_vertices: 8\ndensity: 20kg/m3" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
printf "nr_edges: 6\nnr_vertices: 4\ndensity: 10kg/m3" | tagit record figure "color=green, shape=tetrahedron, weight=5kg" > /dev/null
tagit parse add figure nr_edges "awk '/^nr_edges/{print \$NF}'" > /dev/null
tagit parse add figure nr_vertices "awk '/^nr_vertices/{print \$NF}'" > /dev/null
tagit parse add figure -s nr_vertices result "cat | sed 's/^/nr_vertices: /'" > /dev/null
tagit parse add figure -s nr_edges result "cat | sed 's/^/nr_edges: /'" > /dev/null

printf "IOPS: 20K\nlatency:100us" | tagit record perf "storage=sata_ssd, mem=16GB" > /dev/null
printf "IOPS: 40K\nlatency:10us" | tagit record perf "storage=nvme_ssd, mem=16GB" > /dev/null
printf "IOPS: 60K\nlatency:10us" | tagit record perf "storage=nvme_ssd, mem=32GB" > /dev/null
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
	exit 1
fi
printf "passed\n"

# 2. List tags and data categories
printf "per-exp test.. "

list=$(tagit list figure)
list_gt=$'[figure] List of tags:
- color (green)
- shape (tetrahedron)
- weight (5kg)
[figure] List of data categories:
- raw
- nr_edges
- nr_vertices
- result'

if [ "$list_gt" != "$list" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"

# 3. Fixed tags
printf "fixed value test.. "

rm ~/.tagit/tagit.db

tagit fix figure "color=blue" > /dev/null
echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null

figure_gt=$'[figure] List of tags:
- color (blue)
- shape (sphere)
- weight (10kg)
[figure] List of data categories:
- raw'

figure=$(tagit list figure)

if [ "$figure_gt" != "$figure" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


echo "Test passed"
