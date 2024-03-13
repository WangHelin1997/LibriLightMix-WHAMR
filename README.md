# Generating the LibriLight-Mix dataset

This script supports generating noisy and reverberant 2-speaker mixture audio for training with the Libri-Light dataset, which can be served as training materials for large-scale robust speech separation.

## Python requirements

Requires python 3.8, and the numpy, scipy, pandas, pyroomacoustics, and pysoundfile packages
```sh
$ pip install -r requirements.txt
```

If you cannot install the ```pyroomacoustics``` successfully, you can try:
```sh
$ pip install pyroomacoustics
$ pip install -r requirements.txt
```

## Prerequisites

This requires the [Libri-Light](https://github.com/facebookresearch/libri-light) dataset,
and the [WHAM](http://wham.whisper.ai/) noise corpus.

## Creating LibriLight-Mix

### Creating meta files

```sh
$ python create_filenames.py 
```
Change the following arguments in the script:
* **wham_path**:  Folder where the unzipped wham_noise was downloaded (training set).
* **librilight_path**: Folder where the unzipped Libri-Light data was downloaded.
* **debug**: Whether to process a dummy dataset.
* **SOT**: Whether to process speakers in order (speaker1 speaks earlier than speaker2) for [serialized output training](https://arxiv.org/pdf/2003.12687.pdf).

### Creating reverberation meta files

```sh
$ python run_sample_reverb.py 
```

### Creating mixture files

```sh
$ python create_wham_from_scratch.py --mono \
    --output-dir ./librilight_whamr/ \
    --mode fix \
    --sr 16000 \
    --fixed-len 5
 
```

The arguments for the script are:
* **output-dir**: Where to write the new dataset.
* **mode**: Length of the simulated speech: "fix" for a fixed length, "min" for the minimum length of the two utterences, and "max" for the maximum length of the two utterences.
* **sr**: Sampling rate.
* **fixed-len**: Fixed length in mode "fix".

## Creating LibriLight-Mix parallelly with mulitple CPUs

### Creating meta files

```sh
$ python create_filenames_parallel.py 
```
Change the following arguments in the script:
* **wham_path**:  Folder where the unzipped wham_noise was downloaded (training set).
* **librilight_path**: Folder where the unzipped Libri-Light data was downloaded.
* **savename**: Name of the meta .csv file to save.
* **tag**: Name of the meta .csv folder to save.
* **debug**: Whether to process a dummy dataset.
* **SOT**: Whether to process speakers in order (speaker1 speaks earlier than speaker2) for [serialized output training](https://arxiv.org/pdf/2003.12687.pdf).

### Creating reverberation meta files

```sh
$ python run_sample_reverb_parallel.py 
```
Change the **filelists** according to the **tag**.

### Creating mixture files

```
for i in $(seq 0 51)
do
    python create_wham_from_scratch_parallel.py --mono \
        --output-dir "./LibrilightMix-medium/$i/" \
        --filepath "data/medium/mix_2_spk_filenames_librilight_tr_medium$i.csv" \
        --mode fix \
        --sr 16000 \
        --fixed-len 5
done
```

The arguments for the script are:
* **output-dir**: Where to write the new dataset.
* **filepath**: Name of the saved meta .csv folder.
* **mode**: Length of the simulated speech: "fix" for a fixed length, "min" for the minimum length of the two utterences, and "max" for the maximum length of the two utterences.
* **sr**: Sampling rate.
* **fixed-len**: Fixed length in mode "fix".



## Output data organization

For each utterance in the training (tr) set folder, the following wav files are written:

1. noise: contains the isolated background noise from WHAM!

2. s1_anechoic: isolated data from speaker 1 without reverb, but with appropriate delays to align with s1_reverb

3. s2_anechoic: isolated data from speaker 2 without reverb, but with appropriate delays to align with s2_reverb

4. s1_reverb: isolated data from speaker 1 with reverberation

5. s2_reverb: isolated data from speaker 2 with reverberation

6. mix_single_anechoic: for speech enhancement, contains mixture of s1_anechoic and noise

7. mix_clean_anechoic: clean speech separation for two speakers, contains mixture of s1_anechoic and s2_anechoic.  The relative levels between speakers should match the original libri-light dataset, but the overall level of the mix will be different.

8. mix_both_anechoic: contains mixtures of s1_anechoic, s2_anechoic, and noise

9. mix_single_reverb: for speech enhancement, contains mixture of s1_reverb and noise

10. mix_clean_reverb: clean speech separation for two reverberant speakers, contains a mixture of s1_reverb and s2_reverb.  The relative levels between speakers should match the original libri-light dataset, but the overall level of the mix will be different.

11. mix_both_reverb: contains mixtures of s1_reverb, s2_reverb, and noise


## Reference

https://wham.whisper.ai/WHAMR_README.html
