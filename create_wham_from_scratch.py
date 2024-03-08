import os
import numpy as np
import soundfile as sf
import pandas as pd
from constants import SAMPLERATE
import argparse
from utils import read_scaled_wav, quantize, fix_length, create_wham_mixes
from wham_room import WhamRoom
import multiprocessing
import random

FILELIST_STUB = os.path.join('data', 'mix_2_spk_filenames_librilight_{}.csv')

SINGLE_DIR = 'mix_single'
BOTH_DIR = 'mix_both'
CLEAN_DIR = 'mix_clean'
S1_DIR = 's1'
S2_DIR = 's2'
NOISE_DIR = 'noise'
SUFFIXES = ['_anechoic', '_reverb']
SPLITS = ['tr']

def create_one(i_utt, output_name, wsjmix_df, reverb_param_df, SAMPLE_RATES, output_root, MODE, splt, FIXED_LEN, ch_ind, LEFT_CH_IND):
    wav_dir = 'wav' + str(SAMPLE_RATES)
    output_path = os.path.join(output_root, wav_dir, MODE, splt)
    if not os.path.exists(os.path.join(output_path, NOISE_DIR, output_name)):
        utt_row = reverb_param_df[reverb_param_df['output_filename'] == output_name]
        room = WhamRoom([utt_row['room_x'].iloc[0], utt_row['room_y'].iloc[0], utt_row['room_z'].iloc[0]],
                        [[utt_row['micL_x'].iloc[0], utt_row['micL_y'].iloc[0], utt_row['mic_z'].iloc[0]],
                            [utt_row['micR_x'].iloc[0], utt_row['micR_y'].iloc[0], utt_row['mic_z'].iloc[0]]],
                        [utt_row['s1_x'].iloc[0], utt_row['s1_y'].iloc[0], utt_row['s1_z'].iloc[0]],
                        [utt_row['s2_x'].iloc[0], utt_row['s2_y'].iloc[0], utt_row['s2_z'].iloc[0]],
                        utt_row['T60'].iloc[0])
        room.generate_rirs()
    
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
        noise_path = utt_row['noise_path'].iloc[0]
        noise_snr = 10**(float(utt_row["noise_snr"].iloc[0]) / 20)
        snr_ratio = 0.9/(s1_snr + s2_snr + noise_snr)
        s1 = quantize(read_scaled_wav(s1_path, s1_snr*snr_ratio, s1_start, s1_end, SAMPLE_RATES))
        s2 = quantize(read_scaled_wav(s2_path, s2_snr*snr_ratio, s2_start, s2_end, SAMPLE_RATES))
        s1, s2 = fix_length(s1, s2, s1_tag, s2_tag, MODE, FIXED_LEN, SAMPLE_RATES)
    
        room.add_audio(s1, s2)
        anechoic = room.generate_audio(anechoic=True, fs=SAMPLE_RATES)
        reverberant = room.generate_audio(fs=SAMPLE_RATES)
    
        # Make relative source energy of anechoic sources same with original in mono (left channel) case
        s1_spatial_scaling = np.sqrt(np.sum(s1 ** 2) / np.sum(anechoic[0, LEFT_CH_IND, :] ** 2))
        s2_spatial_scaling = np.sqrt(np.sum(s2 ** 2) / np.sum(anechoic[1, LEFT_CH_IND, :] ** 2))
    
        noise_samples_full = read_scaled_wav(noise_path, noise_snr*snr_ratio, 0, None, SAMPLE_RATES)
    
        if noise_samples_full.shape[0] < s1.shape[0]:
            repeat_factor = (s1.shape[0] // noise_samples_full.shape[0]) + 1
            noise_samples_full = np.tile(noise_samples_full, repeat_factor)
        noise_samples_full = noise_samples_full[:s1.shape[0]]
            
        out_len = s1.shape[0]
    
        s1_anechoic = anechoic[0, ch_ind, :out_len].T * s1_spatial_scaling
        s2_anechoic = anechoic[1, ch_ind, :out_len].T * s2_spatial_scaling
        s1_reverb = reverberant[0, ch_ind, :out_len].T * s1_spatial_scaling
        s2_reverb = reverberant[1, ch_ind, :out_len].T * s2_spatial_scaling
    
        sources = [(s1_anechoic, s2_anechoic), (s1_reverb, s2_reverb)]
        for i_sfx, (sfx, source_pair) in enumerate(zip(SUFFIXES, sources)):
            s1_samples, s2_samples, noise_samples = source_pair[0], source_pair[1], noise_samples_full
            mix_clean, mix_single, mix_both = create_wham_mixes(s1_samples, s2_samples, noise_samples)
    
            # write audio
            samps = [mix_clean, mix_single, mix_both, s1_samples, s2_samples]
            dirs = [CLEAN_DIR, SINGLE_DIR, BOTH_DIR, S1_DIR, S2_DIR]
            for dir, samp in zip(dirs, samps):
                sf.write(os.path.join(output_path, dir+sfx, output_name), samp,
                            SAMPLE_RATES, subtype='FLOAT')
    
            if i_sfx == 0: # only write noise once as it doesn't change between anechoic and reverberant
                sf.write(os.path.join(output_path, NOISE_DIR, output_name), noise_samples,
                            SAMPLE_RATES, subtype='FLOAT')
    
        if (i_utt + 1) % 500 == 0:
            print('Completed {} of {} utterances'.format(i_utt + 1, len(wsjmix_df)))
                    
                
def create_wham(args, output_root):
    MONO = args.mono
    MODE = args.mode
    FIXED_LEN = args.fixed_len
    SAMPLE_RATES = args.sr
    
    LEFT_CH_IND = 0
    if MONO:
        ch_ind = LEFT_CH_IND
    else:
        ch_ind = [0, 1]

    reverb_param_stub = os.path.join('data', 'reverb_params_librilight_{}.csv')

    for splt in SPLITS:

        wsjmix_path = FILELIST_STUB.format(splt)
        wsjmix_df = pd.read_csv(wsjmix_path)

        reverb_param_path = reverb_param_stub.format(splt)
        reverb_param_df = pd.read_csv(reverb_param_path)

        wav_dir = 'wav' + str(SAMPLE_RATES)
        output_path = os.path.join(output_root, wav_dir, MODE, splt)
        for sfx in SUFFIXES:
            os.makedirs(os.path.join(output_path, CLEAN_DIR+sfx), exist_ok=True)
            os.makedirs(os.path.join(output_path, SINGLE_DIR+sfx), exist_ok=True)
            os.makedirs(os.path.join(output_path, BOTH_DIR+sfx), exist_ok=True)
            os.makedirs(os.path.join(output_path, S1_DIR+sfx), exist_ok=True)
            os.makedirs(os.path.join(output_path, S2_DIR+sfx), exist_ok=True)
        os.makedirs(os.path.join(output_path, NOISE_DIR), exist_ok=True)

        utt_ids = wsjmix_df['output_filename']

        cmds = []
        for i_utt, output_name in enumerate(utt_ids):
            cmds.append((i_utt, output_name, wsjmix_df, reverb_param_df, SAMPLE_RATES, output_root, MODE, splt, FIXED_LEN, ch_ind, LEFT_CH_IND))
        print('Totally {} utterances'.format(len(cmds)))
        random.shuffle(cmds) # For parallel CPU processing, which can run several scripts at the same time.
        with multiprocessing.Pool(processes=20) as pool:
            pool.starmap(create_one, cmds)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Output directory for writing wsj0-2mix 8 k Hz and 16 kHz datasets.')
    parser.add_argument('--mode', type=str, required=True,
                    help='Simulated mode of data: fix, max or min')
    parser.add_argument('--sr', type=int, default=16000,
                help='Sampling rate')
    parser.add_argument('--fixed-len', type=float, default=5,
            help='Fixed length of simulated speech')
    parser.add_argument('--mono', action='store_true', help='Generate mono audio, set false for stereo audio, not test yet')

    args = parser.parse_args()
    print('All arguments:', args)
    os.makedirs(args.output_dir, exist_ok=True)
    create_wham(args, args.output_dir)
