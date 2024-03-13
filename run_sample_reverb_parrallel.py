import numpy as np
import pandas as pd
import os
from sample_reverb import draw_params
import random
import glob

SPLIT_NAMES = {'Train': 'tr'}

SEED = 17
np.random.seed(SEED)
random.seed(SEED)

filelists = glob.glob('data/medium/*.csv')
for filelist in filelists:
    FILELIST_STUB = os.path.join('data','medium',filelist)
    REVERB_STUB = FILELIST_STUB.replace('mix_2_spk_filenames', 'reverb_params')

    for split_long, split_short in SPLIT_NAMES.items():
        print('Running {} Set'.format(split_long))
        filelist_path = FILELIST_STUB.format(split_short)
        filelist_df = pd.read_csv(filelist_path)
        utt_ids = list(filelist_df['output_filename'])

        utt_list, param_list = [], []
        for utt in utt_ids:
            mic_sp = random.randint(15, 17)
            rev_lvl = random.choice(["high","medium","low"])
            room_params = draw_params(mic_sp/100., rev_lvl)

            room_dim = room_params[0]
            mics = room_params[1]
            s1 = room_params[2]
            s2 = room_params[3]
            T60 = room_params[4]

            param_dict = { 'room_x' : room_dim[0],
                        'room_y' : room_dim[1],
                        'room_z' : room_dim[2],
                        'micL_x' : mics[0][0],
                        'micL_y' : mics[0][1],
                        'micR_x' : mics[1][0],
                        'micR_y' : mics[1][1],
                        'mic_z' : mics[0][2],
                        's1_x' : s1[0],
                        's1_y' : s1[1],
                        's1_z' : s1[2],
                        's2_x' : s2[0],
                        's2_y' : s2[1],
                        's2_z' : s2[2],
                        'T60' : T60 }

            utt_list.append(utt)
            param_list.append(param_dict)

        reverb_param_df = pd.DataFrame(data=param_list, index=utt_list,
                                    columns=['room_x', 'room_y', 'room_z', 'micL_x', 'micL_y', 'micR_x', 'micR_y', 'mic_z', 's1_x', 's1_y', 's1_z', 's2_x', 's2_y', 's2_z', 'T60'])
        reverb_param_path = REVERB_STUB.format(split_short)
        reverb_param_df.to_csv(reverb_param_path, index=True, index_label='output_filename')
