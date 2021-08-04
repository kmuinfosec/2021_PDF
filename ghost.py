import os
import pickle
import random
import sys

import lightgbm
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm


def main(args):
    if len(args) == 1:
        mal_benign = float(input("Input Benign multiple : "))
        test_size = float(input("Input test ratio : "))
        file_threshold = float(input("Input file size threshold : "))
    else:
        mal_benign = float(args[1])
        test_size = float(args[2])
        file_threshold = float(args[3])

    # data.csv contains where pdf file is located and their label
    # for example...
    # D:\pdf\ben\fffd11598cf97c48b6b1a8a514b9611d.pdf,0
    # D:\pdf\ben\fffdb099f0eb8ea3a56414a7e35f867a.pdf,0
    # D:\pdf\ben\fffde757501c26c60012f3f4ad9b7471.pdf,0
    # D:\pdf\ben\fffe138d6794085c246ce2de61d915bc.pdf,0
    # D:\pdf\ben\ffff534035da87f25c0c65e1042c2a7b.pdf,0
    # D:\pdf\ben\ffff98eb1796929dbc8df697ea1bc771.pdf,0
    # D:\pdf\pdf2021\00000c1d5dcf7543499a66493c3b6bc0.vir,1
    # D:\pdf\pdf2021\00003a0fae3666372922a584b6c2ac1d.vir,1
    # D:\pdf\pdf2021\0001751330fa28febe201ed3a0b8e1c2.vir,1
    # D:\pdf\pdf2021\0001b3b272ad344e18266af45e9a1a26.vir,1
    # D:\pdf\pdf2021\0002c846da0018b85eb59bb5d109a063.vir,1
    # D:\pdf\pdf2021\000317e4e5314b88fba260e9038c85bb.vir,1
    # D:\pdf\pdf2021\00038af3bfc29f22e6e99a1774d49c54.vir,1
    # D:\pdf\pdf2021\0003f697b95d438878c9222b6bb3db16.vir,1
    csv = pd.read_csv("../data.csv")
    ben_csv = csv[csv['label'] == 0]
    mal_csv = csv[csv['label'] == 1]

    # filter out whether pdf file is real pdf file and contains javascript or beyond file size threshold
    filter_set = set()
    paths = list(ben_csv['md5']) + (list(mal_csv['md5']))
    with open('./js_container', 'rb') as f:
        js_set = pickle.load(f)
    with open('./pdf_container', 'rb') as f:
        pdf_set = pickle.load(f)
    js_excluded = 0
    pdf_excluded = 0
    for i in tqdm(paths):
        file_size = os.path.getsize(i)
        if file_size < file_threshold:
            name, ext = i.split(os.sep)[-1].rsplit(os.extsep, maxsplit=1)
            assert len(name) == len('00003a0fae3666372922a584b6c2ac1d')
            if name in pdf_set:
                if name in js_set:
                    filter_set.add(name)
                else:
                    js_excluded += 1
            else:
                pdf_excluded += 1
    print(f"{pdf_excluded} files are excluded cause not pdf")
    print(f"{js_excluded} files are excluded via js")

    # Loading features
    labels = []
    features = []
    file_names = []
    mal_feature_path = r'D:\pdf\our_idea\mal_feature'
    ben_feature_path = r'D:\pdf\our_idea\ben_feature'

    print("Loading features...")
    ben_paths = []
    mal_paths = []
    for label, base in enumerate([ben_feature_path, mal_feature_path]):
        for file in os.listdir(base):
            name, ext = file.split(os.sep)[-1].rsplit(os.extsep, maxsplit=1)
            assert len(name) == len('00003a0fae3666372922a584b6c2ac1d')
            if name in filter_set:
                if label:
                    mal_paths.append(base + os.sep + file)
                else:
                    ben_paths.append(base + os.sep + file)
    print(f"mal: {len(mal_paths)}, ben: {len(ben_paths)}")
    for i in ben_paths:
        print(i)
    ben_paths = random.sample(ben_paths, k=min(len(ben_paths), int(len(mal_paths) * mal_benign)))
    for label, base in enumerate([ben_paths, mal_paths]):
        for i in tqdm(base):
            name = i.split(os.sep)[-1].split(os.extsep)[0]
            with open(i, 'rb') as f:
                features.append(pickle.load(f))
                labels.append(label)
                file_names.append(name)
    mal_benign = len(mal_paths) / len(ben_paths)
    print(f"Benign: {len(ben_paths)}, Malware: {len(mal_paths)} are used")

    files_train, files_test, x_train, x_test, y_train, y_test = train_test_split(file_names, features, labels,
                                                                                 test_size=test_size, random_state=486)
    assert len(files_train) == len(x_train) == len(y_train)

    # Training Model
    model = RandomForestClassifier(n_jobs=16, random_state=486)
    print("Training model...")
    model.fit(x_train, y_train)
    save_path = f"{os.curdir}{os.sep}model_{test_size:.3f}_{mal_benign:.3f}{os.extsep}dat"
    with open(save_path, 'wb') as f:
        pickle.dump(model, f)
        print(f"Model saved at {save_path}")

    # Eval Model
    print("\nEvaluating model...")
    result = model.predict(x_test)
    print("\nScore")
    with open("scores_rf.txt", 'a') as f:
        f.write(
            f"Benign: {len(ben_paths)}, Malware: {len(mal_paths)} || Train: {len(x_train)}, Test: {len(x_test)} || File Size : {file_threshold}\n")
        for i in [accuracy_score, precision_score, recall_score, f1_score]:
            score = i(result, y_test)
            print(f"{i.__name__} : {score:5f}")
            f.write(f"{i.__name__} : {score:5f}\n")

    # Return wrong files hash and label
    with open("./wrong_files.csv", 'w', encoding='utf-8') as f:
        f.write("hash,label,predict\n")
        for i in range(len(files_test)):
            if result[i] != y_test[i]:
                f.write(f"{files_test[i].split(os.extsep)[0]},{y_test[i]},{result[i]}\n")


if __name__ == '__main__':
    main(sys.argv)
