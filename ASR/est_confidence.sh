#!/bin/bash

audio_id=`cut -d ' ' -f 1 recognition/wav.scp`
lattice-to-fst --acoustic-scale=0.1 --lm-scale=15 --rm-eps=false ark:recognition/lattices.ark "scp,p:echo $audio_id recognition/output.fst|"
fstprint --osymbols=models/GMM-HMM/graph/words.txt recognition/output.fst | awk 'NF==5{print}{}' | sort -k5n,5 | cut -f 5 > recognition/likelihoods.txt
number_of_posts=`wc -l recognition/likelihoods.txt | cut -d ' ' -f 1`
if [ $number_of_posts -gt 1 ]
then
post_high=`tail -n 1 recognition/likelihoods.txt`
post_total=`cat recognition/likelihoods.txt | sed "s# #+#g" | bc`
confidence_score=`echo "($post_high-(($post_total-$post_high)/($number_of_posts-1)))/($post_total/$number_of_posts)" | bc`
else
confidence_score=1
fi
echo $confidence_score > recognition/confidence_score.txt
