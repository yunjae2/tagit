#!/bin/bash

# 1. rename test
# 1-1. basic
printf "Rename test 1 (w/o conflict).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit exp rename figure fig > /dev/null
list=$(tagit list)
list_gt=$'fig'

report=$(tagit report fig)
report_gt=$'[fig] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[fig] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[fig] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit 1
fi

if [ "$list_gt" != "$list" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 1-2. conflict
printf "Rename test 2 (w/ conflict).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

echo "A red ball" | tagit record fig "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record fig "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record fig "color=green, shape=sphere, weight=5kg" > /dev/null

report_gt=$(tagit report figure)
list_gt=$(tagit list figure)

rename_gt=$'Error: fig already exists'
rename=$(tagit exp rename figure fig)

report=$(tagit report figure)
list=$(tagit list figure)

if [ "$rename_gt" != "$rename" ]
then
	printf "failed\n"
	exit 1
fi

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit 1
fi

if [ "$list_gt" != "$list" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 2. Remove
printf "Exp removal test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit exp remove figure > /dev/null
report=$(tagit report figure)
report_gt=$'Error: no such experiment
List of experiments:'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 3. Clean
printf "Exp clean test.. "

printf "IOPS: 20K\nlatency: 100us" | tagit record perf "storage=sata_ssd, mem=16GB" > /dev/null
printf "IOPS: 40K\nlatency: 10us" | tagit record perf "storage=nvme_ssd, mem=16GB" > /dev/null
printf "IOPS: 60K\nlatency: 10us" | tagit record perf "storage=nvme_ssd, mem=32GB" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null
tagit exp clean perf > /dev/null

report=$(tagit report perf)
report_gt=$''
list=$(tagit list perf)
list_gt=$'[perf] List of tags:
- storage
- mem
[perf] List of data categories:
- raw
- iops
- latency'
parse=$(tagit parse list perf)
parse_gt=$'  id  rule                         src    dest     updated
----  ---------------------------  -----  -------  ---------
   0  awk \'/^IOPS/{print $NF}\'     raw    iops     False
   1  awk \'/^latency/{print $NF}\'  raw    latency  False'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit 1
fi
if [ "$list_gt" != "$list" ]
then
	printf "failed\n"
	exit 1
fi
if [ "$parse_gt" != "$parse" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


echo "Test passed"
