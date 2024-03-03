# Generating the LibriLight-Mix dataset

## Python requirements

Requires python 3.7, and the numpy, scipy, pandas, pyroomacoustics, and pysoundfile packages
```sh
$ pip install -r requirements.txt
```

## Prerequisites

This requires the [Libri-Light](https://github.com/facebookresearch/libri-light) dataset,
and the [WHAM](http://wham.whisper.ai/) noise corpus.


## Creating LibriLight-Mix

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

For each utterance in the training (tr) set folder, the following wav files are written:

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


## Reference

https://wham.whisper.ai/WHAMR_README.html
