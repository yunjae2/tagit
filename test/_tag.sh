#!/bin/bash

# 1. rename test
# 1-1. basic
printf "Rename test 1 (w/o conflict).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit tag rename figure color colour > /dev/null
report=$(tagit report figure)
report_gt=$'[figure] (colour=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (colour=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (colour=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit 1
fi

list=$(tagit list figure)
list_gt=$'[figure] List of tags:
- colour (green)
- shape (sphere)
- weight (5kg)
[figure] List of data categories:
- raw'

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

report_gt=$(tagit report figure)
list_gt=$(tagit list figure)

rename_gt=$'Error: shape already exists'
rename=$(tagit tag rename figure color shape)

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


echo "Test passed"
