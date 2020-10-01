#!/bin/bash

pushd $(dirname $0) > /dev/null

for t in _*;
do
	fail=true

	echo "# $t"
	./$t || break
	echo ""

	fail=false
done

if [ "$fail" = false ]
then
	echo "Test all passed"
fi

popd > /dev/null
