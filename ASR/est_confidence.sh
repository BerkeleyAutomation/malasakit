#!/bin/bash

lattices=$1
word_symbol_table=$2
conf_eq_no=$3

audio_id=`cut -d ' ' -f 1 recognition/wav.scp`
$cmd "recognition/logs/lattice_to_fst.log" \
  lattice-to-fst --acoustic-scale=0.1 --lm-scale=15 --rm-eps=false "$lattices" "scp,p:echo $audio_id recognition/output.fst|"
fstprint --osymbols=$word_symbol_table recognition/output.fst | awk 'NF==5{print}{}' | sort -k5n,5 | cut -f 5 > recognition/likelihoods.txt
number_of_posts=`wc -l recognition/likelihoods.txt | cut -d ' ' -f 1`
if [ $number_of_posts -gt 1 ]
then
post_add=`cat recognition/likelihoods.txt | tr '\n' '+' | sed 's#.$##'`
post_total=`echo $post_add | bc -l`
post_low=`head -n 1 recognition/likelihoods.txt`
post_high=`tail -n 1 recognition/likelihoods.txt`
#confidence_score_1=`echo "$post_low/$post_total" | bc -l`
#confidence_score=`echo "1 / ( $post_high - $post_low )" | bc -l`

while read orig_score
do
	if [ "$conf_eq_no" -eq 1 ]; then
		norm_confidence_score=`echo "($post_high-$orig_score)/($post_high-$post_low)" | bc -l`
	elif [ "$conf_eq_no" -eq 2 ]; then
		norm_confidence_score=`echo "e((-$orig_score/1000)*l(10))" | bc -l`
	fi
	echo "$norm_confidence_score"
done < "recognition/likelihoods.txt" > "recognition/norm_likelihoods.txt"

conf_high_1=`head -n 1 recognition/norm_likelihoods.txt`
conf_high_2=`head -n 2 recognition/norm_likelihoods.txt | tail -n 1`
confidence_score=`echo "(($conf_high_1-$conf_high_2)/$conf_high_1)" | bc -l`
else
confidence_score=1
fi
echo $confidence_score > recognition/confidence_score.txt
