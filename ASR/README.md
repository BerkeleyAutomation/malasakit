Directory for ASR

Instructions for install:

1. Install kaldi from here: https://github.com/kaldi-asr/kaldi
2. Create a folder "malasakit-digits" in the egs directory under kaldi-master
3. Put all the files from ASR folder in this github into the malasakit-digits folder.


Usage of ASR:

. ./recognize.sh "example.wav"



input: example.wav

output: recognition/output.txt

output.txt is in this format: <recognized_digit> <confidence_value>

confidence value ranges from 0 to 1

issue: confidence value always outputs 1 so it needs to be calibrated
