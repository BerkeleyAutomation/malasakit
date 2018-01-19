# Defining Kaldi root directory
export KALDI_ROOT=$(pwd)/../..

# Setting paths to useful tools
export PATH=$PWD/utils/:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/tools/openfst-1.6.2/bin:$KALDI_ROOT/src/lmbin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lm/:$KALDI_ROOT/src/sgmmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin:$KALDI_ROOT/src/latbin/:$KALDI_ROOT/src/onlinebin/:$KALDI_ROOT/src/gst-plugin/:$KALDI_ROOT/tools/portaudio/install/lib:$PWD:$PATH

# Variable that stores path to MITLM library
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/tools/mitlm-svn/lib

# Variable needed for proper data sorting
export LC_ALL=C
