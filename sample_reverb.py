import numpy as np
from numpy.random import uniform

def draw_params(mic_width, reverb_level):

    room_dim = np.array([uniform(5, 10),
                         uniform(5, 10),
                         uniform(3, 4)])

    center = np.array([room_dim[0]/2 + uniform(-0.2, 0.2),
                       room_dim[1]/2 + uniform(-0.2, 0.2),
                       uniform(0.9, 1.8)])

    mic_theta = uniform(0, 2*np.pi)
    mic_offset = np.array([np.cos(mic_theta) * mic_width/2,
                           np.sin(mic_theta) * mic_width/2,
                           0])
    mics = np.array([center + mic_offset,
                     center - mic_offset])

    s1_dist = uniform(0.66, 2)
    s1_theta = uniform(0, 2*np.pi)
    s1_height = uniform(0.9, 1.8)
    s1_offset = np.array([np.cos(s1_theta) * s1_dist,
                          np.sin(s1_theta) * s1_dist,
                          s1_height - center[2]])
    s1 = center + s1_offset

    s2_dist = uniform(0.66, 2)
    s2_theta = uniform(0, 2*np.pi)
    s2_height = uniform(0.9, 1.8)
    s2_offset = np.array([np.cos(s2_theta) * s2_dist,
                          np.sin(s2_theta) * s2_dist,
                          s2_height - center[2]])
    s2 = center + s2_offset

    if reverb_level == "high":
        T60 = uniform(0.4, 1.0)
    elif reverb_level == "medium":
        T60 = uniform(0.2, 0.6)
    elif reverb_level == "low":
        T60 = uniform(0.1, 0.3)

    return [room_dim, mics, s1, s2, T60]
