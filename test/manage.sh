#!/bin/bash

# 1.1. Delete specific row (1 row)
printf "Basic removal test 1 (single record).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit manage figure -r "color=red"
report=$(tagit report figure)
report_gt=$'[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 1.2. Delete specic row (multi-tag)
printf "Basic removal test 2 (multiple tags).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit manage figure -r "shape=sphere, weight=10kg"
report=$(tagit report figure)
report_gt=$'[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 1.3. Delete specic row (two rows)
printf "Basic removal test 3 (multiple records).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit manage figure -r "weight=10kg"
report=$(tagit report figure)
report_gt=$'[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 1.4. Delete specic row (multi-value tags)
printf "Basic removal test 4 (multi-value tags).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit manage figure -r "color=red|yellow"
report=$(tagit report figure)
report_gt=$'[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"


# 2. Delete all
printf "Exp removal test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit manage figure -d
report=$(tagit report figure)
report_gt=$'Error: no such experiment
List of experiments:'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"


echo "Test passed"
