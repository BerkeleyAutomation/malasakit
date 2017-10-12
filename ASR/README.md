Directory for ASR

Instructions for install:

1. Install kaldi from here: https://github.com/kaldi-asr/kaldi
2. Create a folder "malasakit-digits" in the egs directory under kaldi-master
3. Put all the files from ASR folder in this github into the malasakit-digits folder.


Usage of ASR:

. ./recognize.sh "example.wav"

input: example.wav
output: recognition/one-best-hypothesis.txt  (word)
        recognition/recognized_digit.txt   (number equivalent of the word)
