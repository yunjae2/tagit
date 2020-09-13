#!/bin/bash

# 1-1. add (all)
printf "Basic parsing test 1.. "
rm ~/.tagit/tagit.db

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=16GB" -- "echo IOPS: 40K && echo latency: 10us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=32GB" -- "echo IOPS: 60K && echo latency: 10us" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null

report=$(tagit report perf)
report_gt=$'[perf] (storage=sata_ssd, mem=16GB)
- raw: IOPS: 20K
latency: 100us
- iops: 20K
- latency: 100us
[perf] (storage=nvme_ssd, mem=16GB)
- raw: IOPS: 40K
latency: 10us
- iops: 40K
- latency: 10us
[perf] (storage=nvme_ssd, mem=32GB)
- raw: IOPS: 60K
latency: 10us
- iops: 60K
- latency: 10us'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 1-2. add (specific)
printf "Basic parsing test 2.. "
rm ~/.tagit/tagit.db

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=16GB" -- "echo IOPS: 40K && echo latency: 10us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=32GB" -- "echo IOPS: 60K && echo latency: 10us" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null

report=$(tagit report perf -d "iops, latency")
report_gt=$'[perf] (storage=sata_ssd, mem=16GB)
- iops: 20K
- latency: 100us
[perf] (storage=nvme_ssd, mem=16GB)
- iops: 40K
- latency: 10us
[perf] (storage=nvme_ssd, mem=32GB)
- iops: 60K
- latency: 10us'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 2. Order independency
printf "Order independency test.. "
rm ~/.tagit/tagit.db

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit report perf > /dev/null
tagit record perf "storage=nvme_ssd, mem=16GB" -- "echo IOPS: 40K && echo latency: 10us" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null
tagit record perf "storage=nvme_ssd, mem=32GB" -- "echo IOPS: 60K && echo latency: 10us" > /dev/null

report=$(tagit report perf)
report_gt=$'[perf] (storage=sata_ssd, mem=16GB)
- raw: IOPS: 20K
latency: 100us
- iops: 20K
- latency: 100us
[perf] (storage=nvme_ssd, mem=16GB)
- raw: IOPS: 40K
latency: 10us
- iops: 40K
- latency: 10us
[perf] (storage=nvme_ssd, mem=32GB)
- raw: IOPS: 60K
latency: 10us
- iops: 60K
- latency: 10us'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 3-1. conflict test
printf "Conflict test 1.. "
rm ~/.tagit/tagit.db

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
parse=$(tagit parse add perf raw "awk '/^IOPS/{print \$NF}'")
parse_gt="Error: deriving a recorded data category directly"

if [ "$parse_gt" != "$parse" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 3-2. conflict test
printf "Conflict test 2.. "
rm ~/.tagit/tagit.db

tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
parse=$(tagit record perf "storage=sata_ssd, mem=16GB" -d iops -- "echo 20K")
parse_gt="Error: recording to a derived data category"

if [ "$parse_gt" != "$parse" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 4. list
printf "List test.. "
rm ~/.tagit/tagit.db

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=16GB" -- "echo IOPS: 40K && echo latency: 10us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=32GB" -- "echo IOPS: 60K && echo latency: 10us" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null

report=$(tagit parse list perf | tail -n 2)
report_gt=$'   0  awk \'/^IOPS/{print $NF}\'     raw    iops     True
   1  awk \'/^latency/{print $NF}\'  raw    latency  True'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 5-1. remove (all)
printf "Remove test 1.. "
rm ~/.tagit/tagit.db

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=16GB" -- "echo IOPS: 40K && echo latency: 10us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=32GB" -- "echo IOPS: 60K && echo latency: 10us" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null

tagit report perf > /dev/null
tagit parse remove perf -a > /dev/null

report=$(tagit parse list perf | awk 'NR >= 3')
report_gt=$''

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 5-2. remove (specific)
printf "Remove test 2.. "
rm ~/.tagit/tagit.db

tagit record perf "storage=sata_ssd, mem=16GB" -- "echo IOPS: 20K && echo latency: 100us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=16GB" -- "echo IOPS: 40K && echo latency: 10us" > /dev/null
tagit record perf "storage=nvme_ssd, mem=32GB" -- "echo IOPS: 60K && echo latency: 10us" > /dev/null
tagit parse add perf iops "awk '/^IOPS/{print \$NF}'" > /dev/null
tagit parse add perf latency "awk '/^latency/{print \$NF}'" > /dev/null

tagit report perf > /dev/null
tagit parse remove perf 0 > /dev/null

report=$(tagit parse list perf | awk 'NR >= 3')
report_gt=$'   0  awk \'/^latency/{print $NF}\'  raw    latency  False'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

echo "Test passed"