#!/bin/bash

let i=0;
while true
do
	i=$(( $i+1 ))
	timeout 1200 python exp.py $i
	./cleanup.sh
done



