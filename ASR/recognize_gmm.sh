#!/bin/bash
#
# Converts wav files to digits
#
# txt file that contains the recognized digit is in
# recognition/recognized_digit.txt
#
# txt file that contains the recognized word is in
# recognition/one-best-hypothesis.txt
#
# Usage: . ./recognize_gmm.sh audio_file_name language [ model_version confidence_eqn_no ]
#
# audio_file_name: 	full path of the audio file to be recognized
# language: 		[ eng, fil, ceb, ilk ] (default is fil) eng for English, fil for Filipino, ceb for Cebuano, ilk for Ilokano
# model_version:	(optional, default is tri2) [ tri1, tri2, tri3 ] tri1 for Double delta, tri2 for Double delta with LDA and MLLT, tri3 for Double delta with LDA, MLLT, and SAT
# confidence_eqn_no:    (optional, default is 2) [ 1, 2 ] 1 is logarithmic, 2 is linear
#

. ./cmd.sh
. ./path.sh

audiofile=$1

if [ $# -ge 2 ]; then
	language=$2
else
	language='fil'
fi

if [ $# -ge 3 ]; then
	model_type=$3
else
	model_type='tri2'
fi

if [ $# -ge 4 ]; then
	conf_eq_no=$4
else
	conf_eq_no=2
fi

if [ ! -f $audiofile ]; then
	echo " Error: The audio file does not exist."
	return
fi

if grep -Fxq "$language" languages.txt
then
	echo "The language you used is $language"
else
	echo "The language you entered is not supported. Now using fil."
	language='fil'
fi

if grep -Fxq "$model_type" model_versions.txt
then
	echo "The model you used is $model_type"
else
	echo "The model type you entered is not valid. This argument only take tri1, tri2, and tri3 as an input. Now using tri2."
	model_type='tri2'
fi

if [ $conf_eq_no -gt 2 ]
then
	echo "The confidence equation number you entered is invalid. Now using 2."
	conf_eq_no=2
else
	echo "Using confidence equation number $conf_eq_no"
fi

echo ""

confidence_threshold=0.5
beam=16.0
lattice_beam=8.0
acwt=0.10
model="models/${language}/GMM-HMM/${model_type}/final.mdl"
graph="models/${language}/GMM-HMM/${model_type}/graph/HCLG.fst"
word_symbol_table="models/${language}/GMM-HMM/${model_type}/graph/words.txt"
feat_trans1="models/${language}/GMM-HMM/${model_type}/final.mat"
feat_trans2="models/${language}/GMM-HMM/${model_type}/final.mat"
audio_basename=$( basename $audiofile | cut -d "." -f 1 )

paste -d " " <(echo "$audiofile" | cut -d "." -f 1 | tr "/" "_") <(echo "$audiofile") > recognition/wav_${audio_basename}.scp

#$cmd "recognition/logs/raw_mfcc.log" \
  compute-mfcc-feats --allow_downsample=true --subtract-mean=true --config=conf/mfcc.conf \
  scp:recognition/wav_${audio_basename}.scp ark:- | \
  copy-feats --compress=true ark:- \
  ark,scp:mfcc/raw_mfcc_${audio_basename}.ark,mfcc/raw_mfcc_${audio_basename}.scp

cat mfcc/raw_mfcc_${audio_basename}.scp > recognition/feats_${audio_basename}.scp

if [ $model_type = 'tri2' ]; then
feats="ark,s,cs:copy-feats scp:recognition/feats_${audio_basename}.scp ark:- | splice-feats --left-context=3 --right-context=3 ark:- ark:- | transform-feats "$feat_trans1" ark:- ark:- |"
elif [ $model_type = 'tri3' ]; then
feats="ark,s,cs:copy-feats scp:recognition/feats_${audio_basename}.scp ark:- | splice-feats --left-context=3 --right-context=3 ark:- ark:- | transform-feats "$feat_trans2" ark:- ark:- |"
else
feats="ark,s,cs:copy-feats scp:recognition/feats_${audio_basename}.scp ark:- | add-deltas ark:- ark:- |"
fi

$cmd "recognition/logs/gmm_latgen_${audio_basename}.log" \
  gmm-latgen-faster --beam=$beam --lattice-beam=$lattice_beam \
  --acoustic-scale=$acwt --allow-partial=true --word-symbol-table="$word_symbol_table" \
  "$model" "$graph" "$feats" "ark,t:recognition/lattices_${audio_basename}.ark"

$cmd "recognition/logs/lattice_best_path_${audio_basename}.log" \
  lattice-best-path \
  --word-symbol-table="$word_symbol_table" \
  --acoustic-scale=0.1 \
  --lm-scale=15 \
  ark:recognition/lattices_${audio_basename}.ark \
  ark,t:recognition/one-best_${audio_basename}.tra

. ./est_confidence.sh "ark:recognition/lattices_${audio_basename}.ark" "$word_symbol_table" "$conf_eq_no" "$audio_basename"

# $cmd "recognition/logs/lattice_to_ctm.log" \
#  lattice-to-ctm-conf --decode-mbr=true ark:recognition/lattices.ark recognition/alignments.ctm
# cut -d  " " -f 6 recognition/alignments.ctm > recognition/confidence_score_ctm.txt

perl -x utils/int2sym.pl -f 2- \
"$word_symbol_table" \
recognition/one-best_${audio_basename}.tra \
> recognition/one-best-hypothesis_${audio_basename}.txt

cat recognition/one-best-hypothesis_${audio_basename}.txt | cut -d ' ' -f 2 > recognition/recognized_word_${audio_basename}.txt
. ./num2digits.sh $(cat "recognition/recognized_word_${audio_basename}.txt")> recognition/recognized_digit_${audio_basename}.txt

confidence_value=$(cat "recognition/confidence_score_${audio_basename}.txt")

echo ""

if [ 1 -eq "$(echo "${confidence_value} >= ${confidence_threshold}" | bc)" ]
then
	echo "Success!"
else
	echo "Warning: The confidence value is too low!"
fi

echo ""
echo "audio file = $(echo $audiofile)"
echo "recognized word = $(cat recognition/recognized_word_${audio_basename}.txt)"
echo "recognized digit = $(cat recognition/recognized_digit_${audio_basename}.txt)"
echo "confidence score = $(cat recognition/confidence_score_${audio_basename}.txt)"

#rm -rf mfcc/raw_mfcc.scp mfcc/raw_mfcc.ark recognition/wav.scp recognition/lattices.ark recognition/one-best.tra recognition/one-best-hypothesis.txt recognition/recognized_word.txt recognition/feats.scp
