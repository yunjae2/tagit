#!/bin/bash

# 1. Basic test
printf "Basic report test.. "

rm ~/.tagit/tagit.db

tagit record figure "color=red, shape=sphere, weight=10kg" -- "echo A red ball" > /dev/null
tagit record figure "color=yellow, shape=cube, weight=10kg" -- "echo A yellow box" > /dev/null
tagit record figure "color=green, shape=sphere, weight=5kg" -- "echo A green ball" > /dev/null

report=$(tagit report figure)
report_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=yellow, shape=cube, weight=10kg)
- raw: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 2. multi-value tags
printf "Multi-value tag test.. "

rm ~/.tagit/tagit.db

tagit record figure "color=red, shape=sphere, weight=10kg" -- "echo A red ball" > /dev/null
tagit record figure "color=yellow, shape=cube, weight=10kg" -- "echo A yellow box" > /dev/null
tagit record figure "color=green, shape=sphere, weight=5kg" -- "echo A green ball" > /dev/null

report=$(tagit report figure "color=red|green")
report_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: A red ball
[figure] (color=green, shape=sphere, weight=5kg)
- raw: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 3-1. data category test (all)
printf "Data category test 1.. "

rm ~/.tagit/tagit.db

tagit record figure "color=red, shape=sphere, weight=10kg" -d result1 -- "echo A red ball" > /dev/null
tagit record figure "color=yellow, shape=cube, weight=10kg" -d result2 -- "echo A yellow box" > /dev/null
tagit record figure "color=green, shape=sphere, weight=5kg" -d result3 -- "echo A green ball" > /dev/null

report=$(tagit report figure)
report_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- raw: 
- result1: A red ball
- result2: 
- result3: 
[figure] (color=yellow, shape=cube, weight=10kg)
- raw: 
- result1: 
- result2: A yellow box
- result3: 
[figure] (color=green, shape=sphere, weight=5kg)
- raw: 
- result1: 
- result2: 
- result3: A green ball'

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 3. data category test (specific)
printf "Data category test 2.. "

rm ~/.tagit/tagit.db

tagit record figure "color=red, shape=sphere, weight=10kg" -d result1 -- "echo A red ball" > /dev/null
tagit record figure "color=yellow, shape=cube, weight=10kg" -d result2 -- "echo A yellow box" > /dev/null
tagit record figure "color=green, shape=sphere, weight=5kg" -d result3 -- "echo A green ball" > /dev/null

report=$(tagit report figure -d result2)
report_gt=$'[figure] (color=red, shape=sphere, weight=10kg)
- result2: 
[figure] (color=yellow, shape=cube, weight=10kg)
- result2: A yellow box
[figure] (color=green, shape=sphere, weight=5kg)
- result2: '

if [ "$report_gt" != "$report" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 4-1. csv test (all)
printf "csv report test 1.. "

report_csv="test.csv"
report_gt_csv="test_gt.csv"

rm ~/.tagit/tagit.db

tagit record figure "color=red, shape=sphere, weight=10kg" -d result1 -- "echo A red ball" > /dev/null
tagit record figure "color=yellow, shape=cube, weight=10kg" -d result2 -- "echo A yellow box" > /dev/null
tagit record figure "color=green, shape=sphere, weight=5kg" -d result3 -- "echo A green ball" > /dev/null

tagit report figure -c test.csv
echo -e "color,shape,weight,raw,result1,result2,result3\r" > $report_gt_csv
echo -e "red,sphere,10kg,,A red ball,,\r" >> $report_gt_csv
echo -e "yellow,cube,10kg,,,A yellow box,\r" >> $report_gt_csv
echo -e "green,sphere,5kg,,,,A green ball\r" >> $report_gt_csv

is_diff=$(diff $report_csv $report_gt_csv)
rm $report_csv $report_gt_csv
if [ "$is_diff" != "" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

# 4-2. csv test (specified)
printf "csv report test 2.. "

report_csv="test.csv"
report_gt_csv="test_gt.csv"

rm ~/.tagit/tagit.db

tagit record figure "color=red, shape=sphere, weight=10kg" -d result1 -- "echo A red ball" > /dev/null
tagit record figure "color=yellow, shape=cube, weight=10kg" -d result2 -- "echo A yellow box" > /dev/null
tagit record figure "color=green, shape=sphere, weight=5kg" -d result3 -- "echo A green ball" > /dev/null

tagit report figure -c test.csv -d result2
echo -e "color,shape,weight,result2\r" > $report_gt_csv
echo -e "red,sphere,10kg,\r" >> $report_gt_csv
echo -e "yellow,cube,10kg,A yellow box\r" >> $report_gt_csv
echo -e "green,sphere,5kg,\r" >> $report_gt_csv

is_diff=$(diff $report_csv $report_gt_csv)
rm $report_csv $report_gt_csv
if [ "$is_diff" != "" ]
then
	printf "failed\n"
	exit
fi
printf "passed\n"

echo "Test passed"
