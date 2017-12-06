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

paste -d " " <(echo "$audiofile" | cut -d "." -f 1) <(echo "$audiofile") > recognition/wav.scp

compute-mfcc-feats --verbose=2 --config=conf/mfcc.conf \
scp:recognition/wav.scp ark:- | \
copy-feats --compress=true ark:- \
ark,scp:mfcc/raw_mfcc.ark,mfcc/raw_mfcc.scp

cat mfcc/raw_mfcc.scp > recognition/feats.scp

feats='ark,s,cs:copy-feats scp:recognition/feats.scp ark:- | add-deltas ark:- ark:- |'

gmm-latgen-faster --beam=$beam --lattice-beam=$lattice_beam \
--acoustic-scale=$acwt --allow-partial=true --word-symbol-table=models/GMM-HMM/graph/words.txt \
models/GMM-HMM/final.mdl models/GMM-HMM/graph/HCLG.fst "$feats" "ark,t:recognition/lattices.ark"

lattice-best-path \
--word-symbol-table=models/GMM-HMM/graph/words.txt \
ark:recognition/lattices.ark \
ark,t:recognition/one-best.tra

. ./est_confidence.sh

perl -x utils/int2sym.pl -f 2- \
models/GMM-HMM/graph/words.txt \
recognition/one-best.tra \
> recognition/one-best-hypothesis.txt

cat recognition/one-best-hypothesis.txt | cut -d ' ' -f 2 > recognition/recognized_word.txt
. ./num2digits.sh $(cat "recognition/recognized_word.txt")> recognition/recognized_digit.txt

paste -d " " recognition/recognized_digit.txt recognition/confidence_score.txt > recognition/output.txt

<<<<<<< HEAD
<<<<<<< HEAD
rm -rf mfcc/raw_mfcc.scp mfcc/raw_mfcc.ark recognition/wav.scp recognition/lattices.ark recognition/one-best.tra recognition/one-best-hypothesis.txt recognition/recognized_word.txt recognition/feats.scp
=======
rm -rf mfcc/raw_mfcc.scp mfcc/raw_mfcc.ark recognition/wav.scp recognition/lattices.ark recognition/one-best.tra recognition/one-best-hypothesis.txt recognition/recognized_word.txt recognition/feats.scp
>>>>>>> 52df5184e8e543fa33d5385e04700fe946dd1e42
=======
rm -rf mfcc/raw_mfcc.scp mfcc/raw_mfcc.ark recognition/wav.scp recognition/lattices.ark recognition/one-best.tra recognition/one-best-hypothesis.txt recognition/recognized_word.txt recognition/feats.scp
>>>>>>> 5f0d58ac037fc2e50d9d0b695b20987861ef4ffb
