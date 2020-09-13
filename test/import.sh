#!/bin/bash

figure_orig=figure_orig.csv
perf_orig=perf_orig.csv
figure_import=figure_import.csv
perf_import=perf_import.csv

printf "Basic test.. "

# 0. Clean previous data
rm ~/.tagit/tagit.db

# 1. Record some data
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

# 2. Report db
tagit report figure -c $figure_orig > /dev/null
tagit report perf -c $perf_orig > /dev/null

# 3. Export db
tagit export backup.db > /dev/null

# 4. Import db
tagit import -y backup.db > /dev/null
rm backup.db

# 5. Report imported db
tagit report figure -c $figure_import > /dev/null
tagit report perf -c $perf_import > /dev/null

# 6. diff
is_diff=$(diff $figure_orig $figure_import)
if [ "$is_diff" != "" ]
then
	printf "failed\n"
	rm $figure_orig $perf_orig $figure_import $perf_import
	exit
fi

is_diff=$(diff $perf_orig $perf_import)
if [ "$is_diff" != "" ]
then
	printf "failed\n"
	rm $figure_orig $perf_orig $figure_import $perf_import
	exit
fi
printf "passed\n"

rm $figure_orig $perf_orig $figure_import $perf_import

echo "Test passed"