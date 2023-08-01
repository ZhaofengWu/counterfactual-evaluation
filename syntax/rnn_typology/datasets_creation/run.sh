#!/bin/bash

# agreement_marker="na-d"
# add_cases=0
nsubj=1
dobj=1
iobj=1
mark_verb=0
filter_no_attractor=0
filter_attractor=0
filter_obj=0
filter_no_obj=0
filter_obj_att=0
filter_no_obj_att=0

for order in "svo" "sov" "osv" "ovs" "vso" "vos"
do
    for split in "train" "dev" "test" 
    do
        python2 main.py --dataset $split --order $order --nsubj $nsubj --dobj $dobj --iobj $iobj --mark-verb $mark_verb --filter-no-att $filter_no_attractor --filter-att $filter_attractor --filter-obj $filter_obj --filter-no-obj $filter_no_obj --filter-obj-att $filter_obj_att --filter-no-obj-att $filter_no_obj_att

        cp ../datasets/* ../../data/ptb_data/${order}/
    done
done
