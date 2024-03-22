#!/bin/bash

awk 'BEGIN {total=0}; {total+=$1}; END {print total}' <<< $(for element in $(awk '/TITEL/ {print $4}' POTCAR); do
  elemfield=$(awk -v elem=$element 'NR == 6 {for (i=1;i<=NF;i++){ if ($i == elem){ print i } } }' POSCAR)
  elemcount=$(awk -v field=$elemfield 'NR == 7 {print $field}' POSCAR)
  elemelectrons=$(grep -e "TITEL.*${element}.*" -A 10 POTCAR | awk '/ZVAL/ {for(i=1;i<=NF;i++){if($i=="ZVAL"){print $(i+2)}}}')
  awk '{print $1 * $2}' <<< "$elemcount $elemelectrons"
done)
