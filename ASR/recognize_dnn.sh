#!/bin/sh
#
# Converts wav files to digits
#
# txt file that contains the recognized digit is in 
# recognition/recognized_digit.txt
#
# txt file that contains the recognized word is in
# recognition/one-best-hypothesis.txt
#
# Usage: . ./recognize.sh audiofilename
#

audiofile=$1

use_gpu=false
min_active=200
max_active=7000
max_mem=50000000
beam=13.0
lattice_beam=8.0
acwt=0.10
nnet_forward_opts="--no-softmax=true --prior-scale=1.0"
feature_transform=models/DNN-HMM/final.feature_transform
class_frame_counts=models/DNN-HMM/ali_train_pdf.counts
nnet=models/DNN-HMM/final.nnet
model=models/DNN-HMM/final.mdl
fst_graph=models/DNN-HMM/graph/HCLG.fst
word_symbol_table=models/DNN-HMM/graph/words.txt
feature_transform_1=models/DNN-HMM/tri2.mat
feature_transform_2=models/DNN-HMM/tri3.mat

paste -d " " <(echo "$audiofile" | cut -d "." -f 1) <(echo "$audiofile") > recognition/wav.scp

compute-mfcc-feats --verbose=2 --config=conf/mfcc.conf \
scp:recognition/wav.scp ark:- | \
copy-feats --compress=true ark:- \
ark,scp:mfcc/raw_mfcc.ark,mfcc/raw_mfcc.scp

cat mfcc/raw_mfcc.scp > recognition/feats.scp

feats="ark,s,cs:copy-feats ark:mfcc/raw_mfcc.ark  ark:- | splice-feats --left-context=3 --right-context=3 ark:- ark:- | transform-feats $feature_transform_1 ark:- ark:- |"

nnet-forward \
--no-softmax=true --prior-scale=1.0 --feature-transform=$feature_transform --class-frame-counts=$class_frame_counts --use-gpu=false \
"$nnet" "$feats" "ark:recognition/nnet_forward.ark"
#latgen-faster-mapped \
#--min-active=$min_active --max-active=$max_active -max-mem=$max_mem --beam=$beam --lattice-beam=$lattice_beam \
#--acoustic-scale=$acwt --allow-partial=true --word-symbol-table=$word_symbol_table \
#"$model" "$fst_graph" "ark:recognition/nnet_forward.ark" "ark,t:recognition/lattices.ark"

latgen-faster-mapped "$model" "$fst_graph" "ark:recognition/nnet_forward.ark" "ark,t:recognition/lattices.ark"

lattice-to-ctm-conf --decode-mbr=true ark:recognition/lattices.ark recognition/alignments.ctm

lattice-best-path \
--word-symbol-table=$word_symbol_table \
ark:recognition/lattices.ark \
ark,t:recognition/one-best.tra

perl -x utils/int2sym.pl -f 2- \
"$word_symbol_table" \
recognition/one-best.tra \
> recognition/one-best-hypothesis.txt

cat recognition/one-best-hypothesis.txt | cut -d ' ' -f 2 > recognition/recognized_word.txt
. ./num2digits.sh $(cat "recognition/recognized_word.txt")> recognition/recognized_digit.txt

cut -d  " " -f 6 recognition/alignments.ctm > recognition/confidence_value.txt

paste -d " " recognition/recognized_digit.txt recognition/confidence_value.txt > recognition/output.txt
