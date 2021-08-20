import multiprocessing as mp
import os
import pickle
import sys

import numpy as np
from tqdm import tqdm

from Utils import get_entropy, get_file_name_ext


def star(args):
    preprocess(*args)


def preprocess(file_path, out_path):
    with open(file_path, 'rb') as f:
        stream_lengths = []
        entropies = []
        tags = set()
        data = pickle.load(f)
        file_size = data['file_size']
        for i in data['body']:
            for tag in data['body'][i]['tags']:
                tags.add(tag)
            if 'stream' in data['body'][i]:
                stream = data['body'][i]['stream'][0]
                entropies.append(get_entropy(stream))
                stream_lengths.append(len(stream))

    length_sum = sum(stream_lengths)
    feature_vector = [
        # Stream Length Distribution
        length_sum,
        # Stream Length, File Size Ratio
        length_sum / file_size if file_size > 0 else -1,
        # Object Stream Length Standard Deviation
        np.std(stream_lengths) if len(stream_lengths) > 0 else -1,
        # Average Object Stream Length
        length_sum / len(stream_lengths) if len(stream_lengths) > 0 else -1,
        # Object Stream Entropy Distribution
        np.std(entropies) if len(entropies) > 0 else -1,
        # Max Stream Entropy
        max(entropies) if len(entropies) > 0 else -1,
        # Avg Stream Entropy
        sum(entropies) / len(entropies) if len(entropies) > 0 else -1,
        # Object Tag Cardinality
        len(tags) if len(tags) > 0 else -1
    ]
    with open(out_path, 'wb') as f:
        pickle.dump(feature_vector, f)


def main(args: list):
    mp.freeze_support()
    _, parse_dir, output_dir = args

    pickle_path = []
    output_path = []
    for path, dirs, files in os.walk(parse_dir):
        for file in files:
            name, ext = get_file_name_ext(path + os.sep + file)
            if ext == 'pickle':
                pickle_path.append(path + os.sep + file)
                output_path.append(output_dir + os.sep + name + os.extsep + 'pickle')
    with mp.Pool(processes=os.cpu_count() // 2) as pool:
        for _ in tqdm(pool.imap_unordered(star, zip(pickle_path, output_path), chunksize=2048), total=len(pickle_path)):
            pass
        pool.close()
        pool.join()


if __name__ == '__main__':
    main(sys.argv)
