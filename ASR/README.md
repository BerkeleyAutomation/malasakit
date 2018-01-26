Directory for ASR

Instructions for install:

1. Install kaldi from here: https://github.com/kaldi-asr/kaldi
2. Compile kaldi by following instructions in kaldi/tools and then in kaldi/src
3. Create a folder "malasakit-digits" in the egs directory under kaldi-master
4. Put all the files from ASR folder in this github into the malasakit-digits folder.
5. Install sox via sudo apt-get install sox or from here: http://sox.sourceforge.net/
6. Download ASR models from here: https://drive.google.com/open?id=1dw_3mb2DayqznzUDHbwFsUv9v6ekm1FR 
7. Replace malasakit-digits/models with the extracted models folder from the link


Usage of ASR:

Usage: 

First run `. ./path.sh`

Then run `. ./recognize.sh <audio_file_name> <language_choice> [ <model_version> <confidence_eqn_no> ]`

inputs:


audio_file_name: 	full path of the audio file to be recognized

language_choice: 		[ eng, fil, ceb, ilk ] (default is fil) eng for English, fil for Filipino, ceb for Cebuano, ilk for Ilokano

model_version:		(optional, default is tri2) [ tri1, tri2, tri3 ] tri1 for the model trained utilizing double delta features, tri2 for double delta with LDA and MLLT, tri3 for double delta with LDA, MLLT, and SAT

confidence_eqn_no:    	(optional, default is 2) (under experimentation) [ 1, 2 ] 1 is Logarithmic, 2 is Linear


outputs:


recognition/recognized_digit_(audio base name here).txt:	the recognized digit in numerical form

recognition/recognized_word_(audio base name here).txt:		the recognized digit in word form

recognition/confidence_score_(audio base name here).txt:	confidence value [ 0 - 1 ]

recognition/realt_time_factor_(audio base name here).txt	real time factor (processing_time/audio_duration)


P.S. if you do not want real time factor, use recognize_gmm.sh instead
