import os
import numpy as np
import soundfile as sf
import pandas as pd
from constants import SAMPLERATE
import argparse
from utils import read_scaled_wav, quantize, fix_length, create_wham_mixes, append_or_truncate
from wham_room import WhamRoom


FILELIST_STUB = os.path.join('data', 'mix_2_spk_filenames_librilight_{}.csv')

SINGLE_DIR = 'mix_single'
BOTH_DIR = 'mix_both'
CLEAN_DIR = 'mix_clean'
S1_DIR = 's1'
S2_DIR = 's2'
NOISE_DIR = 'noise'
SUFFIXES = ['_anechoic', '_reverb']

MONO = True  # Generate mono audio, change to false for stereo audio
SPLITS = ['tr']
SAMPLE_RATES = ['16k'] # Remove element from this list to generate less data
DATA_LEN = ['max'] # Remove element from this list to generate less data

def create_wham(wham_noise_path, output_root):
    LEFT_CH_IND = 0
    if MONO:
        ch_ind = LEFT_CH_IND
    else:
        ch_ind = [0, 1]

    reverb_param_stub = os.path.join('data', 'reverb_params_librilight_{}.csv')

    for splt in SPLITS:

        wsjmix_path = FILELIST_STUB.format(splt)
        wsjmix_df = pd.read_csv(wsjmix_path)

        # scaling_npz_path = scaling_npz_stub.format(splt)
        # scaling_npz = np.load(scaling_npz_path, allow_pickle=True)

        noise_path = os.path.join(wham_noise_path, splt)

        reverb_param_path = reverb_param_stub.format(splt)
        reverb_param_df = pd.read_csv(reverb_param_path)

        for wav_dir in ['wav' + sr for sr in SAMPLE_RATES]:
            for datalen_dir in DATA_LEN:
                output_path = os.path.join(output_root, wav_dir, datalen_dir, splt)
                for sfx in SUFFIXES:
                    os.makedirs(os.path.join(output_path, CLEAN_DIR+sfx), exist_ok=True)
                    os.makedirs(os.path.join(output_path, SINGLE_DIR+sfx), exist_ok=True)
                    os.makedirs(os.path.join(output_path, BOTH_DIR+sfx), exist_ok=True)
                    os.makedirs(os.path.join(output_path, S1_DIR+sfx), exist_ok=True)
                    os.makedirs(os.path.join(output_path, S2_DIR+sfx), exist_ok=True)
                os.makedirs(os.path.join(output_path, NOISE_DIR), exist_ok=True)

        utt_ids = wsjmix_df['output_filename']

        for i_utt, output_name in enumerate(utt_ids):
            utt_row = reverb_param_df[reverb_param_df['output_filename'] == output_name]
            room = WhamRoom([utt_row['room_x'].iloc[0], utt_row['room_y'].iloc[0], utt_row['room_z'].iloc[0]],
                            [[utt_row['micL_x'].iloc[0], utt_row['micL_y'].iloc[0], utt_row['mic_z'].iloc[0]],
                             [utt_row['micR_x'].iloc[0], utt_row['micR_y'].iloc[0], utt_row['mic_z'].iloc[0]]],
                            [utt_row['s1_x'].iloc[0], utt_row['s1_y'].iloc[0], utt_row['s1_z'].iloc[0]],
                            [utt_row['s2_x'].iloc[0], utt_row['s2_y'].iloc[0], utt_row['s2_z'].iloc[0]],
                            utt_row['T60'].iloc[0])
            room.generate_rirs()

            # read the 16kHz unscaled speech files, but make sure to add all 'max' padding to end of utterances
            # for synthesizing all the reverb tails
            utt_row = wsjmix_df[wsjmix_df['output_filename'] == output_name]
            s1_path = utt_row['s1_path'].iloc[0]
            s2_path = utt_row['s2_path'].iloc[0]
            noise_path = utt_row['noise_path'].iloc[0]
            s1_start = float(utt_row["s1_start"].iloc[0])
            s1_end = float(utt_row["s1_end"].iloc[0])
            s1_tag = float(utt_row["s1_tag"].iloc[0])
            s1_snr = 10**(float(utt_row["s1_snr"].iloc[0]) / 20)
            s2_start = float(utt_row["s2_start"].iloc[0])
            s2_end = float(utt_row["s2_end"].iloc[0])
            s2_tag = float(utt_row["s2_tag"].iloc[0])
            s2_snr = 10**(float(utt_row["s2_snr"].iloc[0]) / 20)
            noise_snr = 10**(float(utt_row["noise_snr"].iloc[0]) / 20)
            snr_ratio = 0.9/(s1_snr + s2_snr + noise_snr)
            s1_temp = quantize(read_scaled_wav(s1_path, s1_snr*snr_ratio, s1_start, s1_end))
            s2_temp = quantize(read_scaled_wav(s2_path, s2_snr*snr_ratio, s2_start, s2_end))
            s1_temp = fix_length(s1_temp, s1_tag)
            s2_temp = fix_length(s2_temp, s2_tag)
            noise_samples_temp = read_scaled_wav(noise_path, noise_snr*snr_ratio)
            if noise_samples_temp.shape[0] < 5*16000:
                noise_samples_temp = np.pad(noise_samples_temp, (0, 5*16000-noise_samples_temp.shape[0]), mode='constant')
            s1_temp, s2_temp, noise_samples_temp = append_or_truncate(s1_temp, s2_temp,
                                                                      noise_samples_temp, 'max',
                                                                      start_samp_16k=0)  # don't pad beginning yet

            room.add_audio(s1_temp, s2_temp)

            anechoic = room.generate_audio(anechoic=True, fs=SAMPLE_RATES)
            reverberant = room.generate_audio(fs=SAMPLE_RATES)

            for sr_i, sr_dir in enumerate(SAMPLE_RATES):
                wav_dir = 'wav' + sr_dir
                if sr_dir == '8k':
                    sr = 8000
                    downsample = True
                else:
                    sr = SAMPLERATE
                    downsample = False

                for datalen_dir in DATA_LEN:
                    output_path = os.path.join(output_root, wav_dir, datalen_dir, splt)

                    utt_row = wsjmix_df[wsjmix_df['output_filename'] == output_name]
                    s1_path = utt_row['s1_path'].iloc[0]
                    s2_path = utt_row['s2_path'].iloc[0]
                    s1_start = float(utt_row["s1_start"].iloc[0])
                    s1_end = float(utt_row["s1_end"].iloc[0])
                    s1_tag = float(utt_row["s1_tag"].iloc[0])
                    s1_snr = 10**(float(utt_row["s1_snr"].iloc[0]) / 20)
                    s2_start = float(utt_row["s2_start"].iloc[0])
                    s2_end = float(utt_row["s2_end"].iloc[0])
                    s2_tag = float(utt_row["s2_tag"].iloc[0])
                    s2_snr = 10**(float(utt_row["s2_snr"].iloc[0]) / 20)
                    noise_snr = 10**(float(utt_row["noise_snr"].iloc[0]) / 20)
                    snr_ratio = 0.9/(s1_snr + s2_snr + noise_snr)
                    s1 = quantize(read_scaled_wav(s1_path, s1_snr*snr_ratio, s1_start, s1_end))
                    s2 = quantize(read_scaled_wav(s2_path, s2_snr*snr_ratio, s2_start, s2_end))
                    s1 = fix_length(s1, s1_tag)
                    s2 = fix_length(s2, s2_tag)

                    # Make relative source energy of anechoic sources same with original in mono (left channel) case
                    s1_spatial_scaling = np.sqrt(np.sum(s1 ** 2) / np.sum(anechoic[sr_i][0, LEFT_CH_IND, :] ** 2))
                    s2_spatial_scaling = np.sqrt(np.sum(s2 ** 2) / np.sum(anechoic[sr_i][1, LEFT_CH_IND, :] ** 2))

                    noise_samples_full = read_scaled_wav(noise_path,
                                                         noise_snr*snr_ratio,
                                                         downsample_8K=downsample, mono=MONO)
                    if datalen_dir == 'max':
                        out_len = len(noise_samples_full)
                    else:
                        out_len = np.minimum(len(s1), len(s2))

                    s1_anechoic = anechoic[sr_i][0, ch_ind, :out_len].T * s1_spatial_scaling
                    s2_anechoic = anechoic[sr_i][1, ch_ind, :out_len].T * s2_spatial_scaling
                    s1_reverb = reverberant[sr_i][0, ch_ind, :out_len].T * s1_spatial_scaling
                    s2_reverb = reverberant[sr_i][1, ch_ind, :out_len].T * s2_spatial_scaling

                    sources = [(s1_anechoic, s2_anechoic), (s1_reverb, s2_reverb)]
                    for i_sfx, (sfx, source_pair) in enumerate(zip(SUFFIXES, sources)):
                        s1_samples, s2_samples, noise_samples = append_or_truncate(source_pair[0], source_pair[1],
                                                                                   noise_samples_full, datalen_dir,
                                                                                   start_samp_16k=0, downsample=False)

                        mix_clean, mix_single, mix_both = create_wham_mixes(s1_samples, s2_samples, noise_samples)

                        # write audio
                        samps = [mix_clean, mix_single, mix_both, s1_samples, s2_samples]
                        dirs = [CLEAN_DIR, SINGLE_DIR, BOTH_DIR, S1_DIR, S2_DIR]
                        for dir, samp in zip(dirs, samps):
                            sf.write(os.path.join(output_path, dir+sfx, output_name), samp,
                                     sr, subtype='FLOAT')

                        if i_sfx == 0: # only write noise once as it doesn't change between anechoic and reverberant
                            sf.write(os.path.join(output_path, NOISE_DIR, output_name), noise_samples,
                                     sr, subtype='FLOAT')

            if (i_utt + 1) % 500 == 0:
                print('Completed {} of {} utterances'.format(i_utt + 1, len(wsjmix_df)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for writing wsj0-2mix 8 k Hz and 16 kHz datasets.')
    parser.add_argument('--wham-noise-root', type=str, required=True,
                        help='Path to the downloaded and unzipped wham folder containing metadata/')
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    create_wham(args.wham_noise_root, args.output_dir)
