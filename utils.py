import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def read_scaled_wav(path, scaling_factor, start=0, end=None, downsample_8K=False, mono=True,sr=16000):
    if end is not None:
        samples, sr_orig = sf.read(path, start=int(start*sr), stop=int(end*sr))
    else:
        samples, sr_orig = sf.read(path)

    if len(samples.shape) > 1 and mono:
        samples = samples[:, 0]

    if downsample_8K:
        samples = resample_poly(samples, 8000, sr_orig)
    
    samples /= np.max(np.abs(samples))
    samples *= scaling_factor
    return samples


def wavwrite_quantize(samples):
    return np.int16(np.round((2 ** 15) * samples))


def quantize(samples):
    int_samples = wavwrite_quantize(samples)
    return np.float64(int_samples) / (2 ** 15)


def wavwrite(file, samples, sr):
    """This is how the old Matlab function wavwrite() quantized to 16 bit.
    We match it here to maintain parity with the original dataset"""
    int_samples = wavwrite_quantize(samples)
    sf.write(file, int_samples, sr, subtype='PCM_16')


def append_or_truncate(s1_samples, s2_samples, noise_samples, min_or_max='max', start_samp_16k=0, downsample=False, fixed_length=80000):
    if downsample:
        speech_start_sample = start_samp_16k // 2
    else:
        speech_start_sample = start_samp_16k

    if min_or_max == 'min':
        speech_end_sample = speech_start_sample + len(s1_samples)
        noise_samples = noise_samples[speech_start_sample:speech_end_sample]
    else:
        speech_end_sample = len(s1_samples) - speech_start_sample
        s1_append = np.zeros_like(noise_samples)
        s2_append = np.zeros_like(noise_samples)
        s1_append[speech_start_sample:len(s1_samples)] = s1_samples[0:speech_end_sample]
        s2_append[speech_start_sample:len(s1_samples)] = s2_samples[0:speech_end_sample]
        s1_samples = s1_append
        s2_samples = s2_append
    s1_samples=s1_samples[:fixed_length]
    s2_samples=s2_samples[:fixed_length]
    noise_samples=noise_samples[:fixed_length]

    return s1_samples, s2_samples, noise_samples


def append_zeros(samples, desired_length):
    samples_to_add = desired_length - len(samples)
    if len(samples.shape) == 1:
        new_zeros = np.zeros(samples_to_add)
    elif len(samples.shape) == 2:
        new_zeros = np.zeros((samples_to_add, 2))
    return np.append(samples, new_zeros, axis=0)


def fix_length(s1, tag, fix_length=5, sr=16000):
    # Fix length
    s1_out = np.zeros(sr*fix_length)
    if s1.shape[0] < fix_length*sr - int(sr*tag) - 1: # avoid out of shape
        s1_out[int(sr*tag):s1.shape[0]+int(sr*tag)] = s1
    else:
        s1_out[int(sr*tag):] = s1[:(sr*fix_length-int(sr*tag))]
    return s1_out


def create_wham_mixes(s1_samples, s2_samples, noise_samples):
    mix_clean = s1_samples + s2_samples
    mix_single = noise_samples + s1_samples
    mix_both = noise_samples + s1_samples + s2_samples
    return mix_clean, mix_single, mix_both