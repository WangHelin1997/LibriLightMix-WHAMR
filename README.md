# Generating the WHAMR! dataset

## Python requirements

Requires python 3.7, and the numpy, scipy, pandas, pyroomacoustics, and pysoundfile packages
```sh
$ pip install -r requirements.txt
```

## Prerequisites

This requires the wsj0 (https://catalog.ldc.upenn.edu/LDC93S6A/) dataset,
and the WHAM noise corpus available here (*http://wham.whisper.ai/*).


## Creating WHAMR

```sh
$ python create_wham_from_scratch.py 
    --wsj0-root /path/to/the/wsj/dataset/ 
    --wham-noise-root /path/to/wham_noise/ 
    --output-dir /path/to/output/directory/ 
 
```

The arguments for the script are:
* **wsj0-root**:  Path to the folder containing wsj0/
* **wham-noise-root**: Folder where the unzipped wham_noise was downloaded.
* **output-dir**: Where to write the new dataset.  In the default configuration the script will write about 444 GB of data.

## Output data organization

For each utterance in the training (tr), validation (cv), and testing (tt) set folders, the following wav files are written:

1. noise: contains the isolated background noise from WHAM!

2. s1_anechoic: isolated data from speaker 1 without reverb, but with appropriate delays to align with s1_reverb

3. s2_anechoic: isolated data from speaker 2 without reverb, but with appropriate delays to align with s2_reverb

4. s1_reverb: isolated data from speaker 1 with reverberation

5. s2_reverb: isolated data from speaker 2 with reverberation

6. mix_single_anechoic: for speech enhancement, contains mixture of s1_anechoic and noise

7. mix_clean_anechoic: clean speech separation for two speakers, contains mixture of s1_anechoic and s2_anechoic.  The relative levels between speakers should match the original wsj0-2mix dataset, but the overall level of the mix will be different.

8. mix_both_anechoic: contains mixtures of s1_anechoic, s2_anechoic, and noise

9. mix_single_reverb: for speech enhancement, contains mixture of s1_reverb and noise

10. mix_clean_reverb: clean speech separation for two reverberant speakers, contains a mixture of s1_reverb and s2_reverb.  The relative levels between speakers should match the original wsj0-2mix dataset, but the overall level of the mix will be different.

11. mix_both_reverb: contains mixtures of s1_reverb, s2_reverb, and noise


## Generating only a data subset 

In the default configuration, the script outputs all possible permutations of the dataset (8 kHz and 16 kHz sampling rate plus max and min style utterance truncation), and writes approximately 444 GB of audio data.

To generate less data, the script can be trivially modified to generate only a specific utterance truncation and/or sampling rate by changing the lines of _create_wham_from_scratch.py_
```sh
SAMPLE_RATES = ['16k', '8k'] # Remove element from this list to generate less data
DATA_LEN = ['max', 'min'] # Remove element from this list to generate less data
```

to
```sh
SAMPLE_RATES = ['8k']
DATA_LEN = ['min']
```
to only generate 8 kHz min.

## Generating stereo data

The WHAM! noise data was recorded with a binaural microphone and the simulated reverberation applied to the speech signals uses a similar stereo array configuration.  
By default _create_wham_from_scratch.py_ outputs only the left channel for both noise and reverberated speech signals, but stereo output can be obtained by changing the following line of _create_wham_from_scratch.py_ 
```sh
MONO = True # Generate mono audio, change to false for stereo audio
```

## Comparison with original WHAM! dataset

The _anechoic_ WHAMR! data has small delays between the speakers in order to align with the spatialized reverberant mixtures.
While these delays mean that _anechoic_ WHAMR! is not identical to WHAM!, in the monophonic case we have trained several models on both WHAM! and _anechoic_ WHAMR! and found that average scale-invariant source to distortion ratio (SI-SDR) on the test set always varies by less than 0.05 dB, so we feel that _anechoic_ WHAMR! results can be compared with those from WHAM!


## Citation
If you find WHAMR! useful, please cite our paper:

```sh
@inproceedings{Maciejewski2020WHAMR,
    title     = {WHAMR!: Noisy and Reverberant Single-Channel Speech Separation},
    author    = {Maciejewski, Matthew and Wichern, Gordon and Le Roux, Jonathan},
    booktitle = {Proc. IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)},
    year      = {2020},
    month     = may
}
```