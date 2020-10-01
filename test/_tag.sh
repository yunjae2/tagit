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
- colour
- shape
- weight
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


# 2. fix test
# 2-1. basic test
printf "Fix test 1 (basic).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
tagit tag fix figure "weight=5kg"
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null

figure_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=None)
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


# 2-2. explicit vs specified
printf "Fix test 2 (override).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
tagit tag fix figure "weight=20kg"
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

figure_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=None)
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


# 2-3. fix before tag creation
printf "Fix test 3 (command order) .. "

rm ~/.tagit/tagit.db

tagit tag fix figure "weight=5kg" > /dev/null
echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null

figure_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

figure=$(tagit report figure "color, shape, weight")

if [ "$figure_gt" != "$figure" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 3. unfix test
# 3-1. basic functionality
printf "Unfix test 1 (basic).. "

rm ~/.tagit/tagit.db

tagit tag fix figure "weight=5kg" > /dev/null
echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
tagit tag unfix figure "weight" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null
echo "A pink ball" | tagit record figure "color=pink, weight=20kg" > /dev/null
echo "A pink box" | tagit record figure "shape=cube" > /dev/null

figure_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=5kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=None)
- raw: A green ball
[figure] (color=pink, shape=None, weight=20kg)
- raw: A pink ball
[figure] (color=None, shape=cube, weight=None)
- raw: A pink box'

figure=$(tagit report figure "color, shape, weight")

if [ "$figure_gt" != "$figure" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"

# 3-2. unfixing the non-existing tag
printf "Unfix test 2 (miss).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null

unfix_gt=$'Error: no such tag
List of tags in figure:
- color
- shape
- weight'

unfix=$(tagit tag unfix figure "volume")

if [ "$unfix_gt" != "$unfix" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 4. Update
# 4-1. Existing tag
printf "Update test 1 (existing tag).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit tag update figure "shape=sphere, weight->20kg, shape->random" > /dev/null
report=$(tagit report figure)
report_gt=$'[figure] (color=red, shape=random, weight=20kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=random, weight=20kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


# 4-2. Non-existing tag
printf "Update test 2 (non-existing tag).. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube, weight=10kg" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere, weight=5kg" > /dev/null

tagit tag update figure "shape=sphere, volume->100L" > /dev/null
report=$(tagit report figure)
report_gt=$'[figure] (color=red, shape=sphere, weight=10kg, volume=100L)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=10kg, volume=None)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg, volume=100L)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"


echo "Test passed"
