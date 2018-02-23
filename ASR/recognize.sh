#!/bin/bash
#
# Converts wav files to digits and computes the realtime factor
#
# txt file that contains the recognized digit is in 
# recognition/recognized_digit.txt
#
# txt file that contains the recognized word is in
# recognition/one-best-hypothesis.txt
#
# Usage: . ./recognize.sh audio_file_name language [ model_version confidence_eqn_no ] 
#
# audio_file_name: 	full path of the audio file to be recognized
# language: 		[ eng, fil, ceb, ilk ] (default is fil) eng for English, fil for Filipino, ceb for Cebuano, ilk for Ilokano
# model_version:	(optional, default is tri2) [ tri1, tri2, tri3 ] tri1 for Double delta, tri2 for Double delta with LDA and MLLT, tri3 for Double delta with LDA, MLLT, and SAT
# confidence_eqn_no:    (optional, default is 2) [ 1, 2 ] 1 is logarithmic, 2 is linear
#

start_time=$(date +%s.%N)

audio_file_name=$1
language=fil
model_version=tri2
confidence_eqn_no=2

if [ $# -ge 2 ]; then
	language=$2
fi

if [ $# -ge 3 ]; then
	model_version=$3
fi

if [ $# -ge 4 ]; then
	confidence_eqn_no=$4
fi

if [ ! -f $audio_file_name ]; then
	echo "Error: The audio file does not exist."
	return
fi

if [ ! -f $(pwd)/../../src/featbin/compute-mfcc-feats ]; then
	echo "Error: Kaldi is not compiled pls follow instructions in kaldi/tools/INSTALL and kaldi/src/INSTALL"
	return
fi

. ./recognize_gmm.sh $audio_file_name $language $model_version $confidence_eqn_no 

end_time=$(date +%s.%N)

asr_runtime=$( echo "$end_time - $start_time" | bc -l )
audio_time=$(soxi -D $audio_file_name)
real_time_factor=$( echo "$asr_runtime/$audio_time" | bc -l)
echo $real_time_factor > recognition/real_time_factor_${audio_basename}
echo "real time factor = $real_time_factor"
