import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


def read_scaled_wav(path, scaling_factor, start=0, end=None, sr=16000, mono=True):
    if end is not None:
        samples, sr_orig = sf.read(path, start=int(start*sr), stop=int(end*sr))
    else:
        samples, sr_orig = sf.read(path)

    if len(samples.shape) > 1 and mono:
        samples = samples[:, 0]

    if sr != sr_orig:
        samples = resample_poly(samples, sr, sr_orig)
    
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


def fix_length(s1, s2, tag1, tag2, mode='fix', fixed_len=5, sr=16000):
    # mode: {'fix', 'min', 'max'}
    # tag: start time
    if mode == 'fix':
        # Fix length
        s1_out, s2_out = np.zeros(int(sr*fixed_len)), np.zeros(int(sr*fixed_len))
        if s1.shape[0] < int(fixed_len*sr) - int(sr*tag1): # avoid out of shape
            s1_out[int(sr*tag1):s1.shape[0]+int(sr*tag1)] = s1
        else:
            s1_out[int(sr*tag1):] = s1[:(int(sr*fixed_len)-int(sr*tag1))]
        if s2.shape[0] < int(fixed_len*sr) - int(sr*tag2): # avoid out of shape
            s2_out[int(sr*tag2):s2.shape[0]+int(sr*tag2)] = s2
        else:
            s2_out[int(sr*tag2):] = s2[:(int(sr*fixed_len)-int(sr*tag2))]
    elif mode == 'min':
        utt_len = np.minimum(s1.shape[0]+int(sr*tag1), s2.shape[0]+int(sr*tag2))
        s1_out, s2_out = np.zeros(utt_len), np.zeros(utt_len)
        s1_out[int(sr*tag1):] = s1[:(utt_len-int(sr*tag1))]
        s2_out[int(sr*tag2):] = s2[:(utt_len-int(sr*tag2))]
    else:  # max
        utt_len = np.maximum(s1.shape[0]+int(sr*tag1), s2.shape[0]+int(sr*tag2))
        s1_out, s2_out = np.zeros(utt_len), np.zeros(utt_len)
        s1_out[int(sr*tag1):s1.shape[0]+int(sr*tag1)] = s1
        s2_out[int(sr*tag2):s2.shape[0]+int(sr*tag2)] = s2
    return s1_out, s2_out


def create_wham_mixes(s1_samples, s2_samples, noise_samples):
    mix_clean = s1_samples + s2_samples
    mix_single = noise_samples + s1_samples
    mix_both = noise_samples + s1_samples + s2_samples
    return mix_clean, mix_single, mix_both
