import csv
import os
import random
import glob
import json
from tqdm import tqdm
import multiprocessing

wham_path = '/data/lmorove1/hwang258/librimix/wham_noise/tr'
librilight_path = '/data/lmorove1/hwang258/librilight/medium'
savename = 'mix_2_spk_filenames_librilight_tr_medium'
tag='medium'
debug=False
SOT=True

SEED=17
random.seed(SEED)

def process_one(i, tag, savename, spks, librilight_path, noise_files, debug, SOT):
    count=0
    os.makedirs(os.path.join('data', tag), exist_ok=True)
    file_path = os.path.join('data', tag, savename+ str(i)+'.csv')
    csvdata = [
    ["output_filename","noise_path","noise_snr","s1_path","s1_start","s1_end","s1_tag","s1_snr","s2_path","s2_start","s2_end","s2_tag","s2_snr"]
    ]
    for spk in spks:
        audiofiles = glob.glob(os.path.join(librilight_path, spk, '**/*.flac'), recursive=True)

        for audiofile in audiofiles:
            with open(audiofile.replace('.flac','.json'), 'r') as file:
                audiodata = json.load(file)
            vads = audiodata["voice_activity"]
            if debug:
                if count > 50:
                    break
            for vad in tqdm(vads):
                if float(vad[1]) - float(vad[0]) > 2.:
                    count+=1
                    another_spk = random.choice([x for x in spks if x != spk])
                    another_audiofiles = glob.glob(os.path.join(librilight_path, another_spk, '**/*.flac'), recursive=True)
                    another_audiofile = random.choice(another_audiofiles)
                    with open(another_audiofile.replace('.flac','.json'), 'r') as file:
                        another_audiodata = json.load(file)
                    another_vads = another_audiodata["voice_activity"]
                    another_vad = random.choice(another_vads)
                    noisefile = random.choice(noise_files)
                    s1_start = random.uniform(0, 0.3) if SOT else random.uniform(0, 0.5)
                    s2_start = random.uniform(0.6, 1.3) if SOT else random.uniform(0, 0.5)
                    s1_snr = random.uniform(-3, 6)
                    s2_snr = random.uniform(-3, 6)
                    noise_snr = random.uniform(-6, 3)
                    csvdata.append([
                        str(count)+'.wav',
                        noisefile,
                        noise_snr,
                        audiofile,
                        vad[0],
                        vad[1],
                        s1_start,
                        s1_snr,
                        another_audiofile,
                        another_vad[0],
                        another_vad[1],
                        s2_start,
                        s2_snr
                        ])
            
        
    # Writing to the CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csvdata)
    print(f'Data has been written to {file_path}')


# Reading all noise files
noise_files = [os.path.abspath(os.path.join(wham_path, file)) for file in os.listdir(wham_path) if file.endswith('.wav')]
spks = [name for name in os.listdir(librilight_path) if os.path.isdir(os.path.join(librilight_path, name)) and not os.path.isfile(os.path.join(librilight_path, name))]
num_subspks = 50
subspks_size = len(spks) // num_subspks

random.shuffle(spks)
# Split the list into subspks
subspks = [spks[i*subspks_size:(i+1)*subspks_size] for i in range(num_subspks)] 

# If there are remaining elements, distribute them among the subspks
if len(spks) % num_subspks != 0:
    remainder = len(spks) % num_subspks
    for i in range(remainder):
        subspks[i].append(spks[-(i+1)])
        spks.pop()
        
cmds = []

for i in range(len(subspks)):
    cmds.append((i, tag, savename, subspks[i], librilight_path, noise_files, debug, SOT))
with multiprocessing.Pool(processes=50) as pool:
    pool.starmap(process_one, cmds)
