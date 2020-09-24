#!/bin/bash

for t in _*;
do
	echo "# $t"
	./$t || break
	echo ""
done

echo "Test all passed"
