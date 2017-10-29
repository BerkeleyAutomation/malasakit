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

max_active=7000
beam=13.0
lattice_beam=6.0
acwt=0.083333

paste -d " " <(echo "$audiofile" | cut -d "." -f 1) <(echo "$audiofile") > recognition/wav.scp

compute-mfcc-feats --verbose=2 --config=conf/mfcc.conf \
scp:recognition/wav.scp ark:- \| \
copy-feats --compress=true ark:- \
ark,scp:mfcc/raw_mfcc.ark,mfcc/raw_mfcc.scp

cat mfcc/raw_mfcc.scp > recognition/feats.scp

feats="ark,s,cs:copy-feats scp:recognition/feats.scp ark:- | add-deltas ark:- ark:- |"

gmm-latgen-faster --max-active=$max_active --beam=$beam --lattice-beam=$lattice_beam \
--acoustic-scale=$acwt --allow-partial=true --word-symbol-table=models/graph/words.txt \
models/final.mdl models/graph/HCLG.fst "$feats" "ark,t:recognition/lattices.ark"

lattice-best-path \
--word-symbol-table=models/graph/words.txt \
ark:recognition/lattices.ark \
ark,t:recognition/one-best.tra

utils/int2sym.pl -f 2- \
models/graph/words.txt \
recognition/one-best.tra \
> recognition/one-best-hypothesis.txt

cat recognition/one-best-hypothesis.txt | . ./num2digits.sh > recognition/recognized_digit.txt
