import math
import multiprocessing as mp
import os
import pickle
import sys
from collections import Counter

import numpy as np
from tqdm import tqdm

'''
Stream Length Distribution
악성 파일의 스트림의 길이가 좀 더 길 거라 예상
Stream Length, File Size Ratio
파일 크기에 비해 스트림의 길이가 길 거라 예상
Object Stream Standard Deviation
한 오브젝트에 공격 코드를 삽입하기 때문에 오브젝트 스트림 길이의 분산이 클 것이라 예상
Stream Entropy Distribution
난독화된 공격코드의 경우 엔트로피가 상대적으로 높을 것이라 예상

'''
BEN_PARSE_PATH = r'E:\Source\pdf\ben'
MAL_PARSE_PATH = r'E:\Source\pdf\mal'
BEN_FEATURE_PATH = r'E:\Source\pdf\ben_feature'
MAL_FEATURE_PATH = r'E:\Source\pdf\mal_feature'


def get_entropy(data):
    if not data:
        return 0.0
    occurrences = Counter(bytearray(data))
    entropy = 0
    for x in occurrences.values():
        p_x = float(x) / len(data)
        entropy -= p_x * math.log(p_x, 2)
    return entropy


def do(file_path):
    file_name = file_path.split(os.sep)[-1].rsplit(os.extsep)[0] + os.extsep + 'pickle'
    with open(file_path, 'rb') as f:
        stream_lengths = []
        entropies = []
        tags = set()
        data = pickle.load(f)
        file_size = data['meta']['file_size']
        for i in data['body']:
            if isinstance(i, int):
                if 'stream' in data['body'][i]:
                    for tag in data['body'][i]['tags']:
                        tags.add(tag)
                    if data['body'][i]['actual_length'] > 0:
                        stream = data['body'][i]['stream']
                        entropies.append(get_entropy(stream))
                        stream_lengths.append(data['body'][i]['actual_length'])

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
    with open(MAL_FEATURE_PATH + os.sep + file_name, 'wb') as f:
        pickle.dump(feature_vector, f)


def main(args):
    if len(args) == 1:
        base_path = input("Please input file path : ")
    else:
        base_path = args[2]
    base_path = MAL_PARSE_PATH

    file_list = []
    for path, dirs, files in os.walk(base_path):
        for file in files:
            name, ext = file.split(os.extsep, maxsplit=1)
            if ext == 'pickle':
                file_list.append(path + os.sep + file)

    with mp.Pool(processes=os.cpu_count() // 2) as pool:
        for _ in tqdm(pool.imap_unordered(do, file_list), total=len(file_list)):
            pass


if __name__ == '__main__':
    main(sys.argv)
