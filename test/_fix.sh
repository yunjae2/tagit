#!/bin/bash

# 1. fix test
# 1-1. explicit vs implicit
printf "Priority test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
tagit fix figure "weight=5kg"
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null

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


# 1-2. explicit vs specified
printf "Override test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
tagit fix figure "weight=20kg"
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


# 1-3. fix before tag creation
printf "Command order test.. "

rm ~/.tagit/tagit.db

tagit fix figure "weight=5kg" > /dev/null
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


# 2. unfix test
# 2-1. basic functionality
printf "Unfix basic test.. "

rm ~/.tagit/tagit.db

tagit fix figure "weight=5kg" > /dev/null
echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
tagit unfix figure "weight" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null
echo "A pink ball" | tagit record figure "color=pink, weight=20kg" > /dev/null
echo "A pink box" | tagit record figure "shape=cube" > /dev/null

figure_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=5kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball
[figure] (color=pink, shape=sphere, weight=20kg)
- raw: A pink ball
[figure] (color=pink, shape=cube, weight=20kg)
- raw: A pink box'

figure=$(tagit report figure "color, shape, weight")

if [ "$figure_gt" != "$figure" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"

# 2-2. unfixing the non-existing tag
printf "Unfix miss test.. "

rm ~/.tagit/tagit.db

echo "A red ball" | tagit record figure "color=red, shape=sphere, weight=10kg" > /dev/null
echo "A yellow box" | tagit record figure "color=yellow, shape=cube" > /dev/null
echo "A green ball" | tagit record figure "color=green, shape=sphere" > /dev/null

unfix_gt=$'Error: no such tag
List of tags in figure:
- color
- shape
- weight'

unfix=$(tagit unfix figure "volume")

if [ "$unfix_gt" != "$unfix" ]
then
	printf "failed\n"
	exit 1
fi
printf "passed\n"

echo "Test passed"
