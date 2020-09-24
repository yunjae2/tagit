#!/bin/bash

# 1. Basic test
printf "Basic test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

figure_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

figure=$(tagit report figure)

if [ "$figure_gt" != "$figure" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 2. Multiple experiment test
printf "multi-experiment test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A low-end machine" | tagit record perf "storage=sata_ssd, mem=16GB" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A mid-end machine" | tagit record perf "storage=nvme_ssd, mem=16GB" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null
echo "A high-end machine" | tagit record perf "storage=nvme_ssd, mem=32GB" > /dev/null

figure_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

perf_gt=$'[perf] (storage=sata_ssd, mem=16GB)
- raw: A low-end machine
[perf] (storage=nvme_ssd, mem=16GB)
- raw: A mid-end machine
[perf] (storage=nvme_ssd, mem=32GB)
- raw: A high-end machine'

figure=$(tagit report figure)
perf=$(tagit report perf)

if [ "$figure_gt" != "$figure" ]
then
	printf "failed\n"
	exit 1
fi
if [ "$perf_gt" != "$perf" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 3. category test
printf "data category test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record -d raw figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record -d cat1 figure "color=yellow, shape=cube, weight=10kg" > /dev/null

cat_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
- cat1: 
[figure] (color=yellow, shape=cube, weight=10kg)
- raw: 
- cat1: A yellow box'
cat=$(tagit report figure)

if [ "$cat_gt" != "$cat" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 4. quietness test
printf "quietness test.. "

rm ~/.tagit/tagit.db

quiet_gt=$'New experiment: [figure]
[figure] New tag added:
- color
- shape
- weight'
quiet=$(echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" -q)

if [ "$quiet_gt" != "$quiet" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 5. Overwrite test
printf "overwrite test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null
echo "A red sphere" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null

figure_gt=$'[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball
[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red sphere'

figure=$(tagit report figure)

if [ "$figure_gt" != "$figure" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"

echo "Test passed"
