import os
import pickle
import random
import sys

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split


def main(args):
    if len(args) == 1:
        mal_benign = 1
        test_size = 0.25
    else:
        mal_benign = float(args[1])
        test_size = float(args[2])

    labels = []
    features = []
    file_names = []
    mal_feature_path = r'E:\Source\pdf\mal_feature'
    ben_feature_path = r'E:\Source\pdf\ben_feature'

    print("Loading features...")
    ben_paths = []
    mal_paths = []
    for label, base in enumerate([ben_feature_path, mal_feature_path]):
        for file in os.listdir(base):
            if label:
                mal_paths.append(base + os.sep + file)
            else:
                ben_paths.append(base + os.sep + file)
    ben_paths = random.sample(ben_paths, k=min(len(ben_paths), int(len(mal_paths) * mal_benign)))
    for label, base in enumerate([ben_paths, mal_paths]):
        for i in base:
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
    print(y_train.count(1), y_train.count(0))
    model = RandomForestClassifier(n_jobs=16, random_state=486)
    print("Training model...")
    model.fit(x_train, y_train)
    save_path = f"{os.curdir}{os.sep}model_{test_size:.3f}_{mal_benign:.3f}{os.extsep}dat"
    with open(save_path, 'wb') as f:
        pickle.dump(model, f)
        print(f"Model saved at {save_path}")

    print("\nEvaluating model...")
    result = model.predict(x_test)
    print("\nScore")
    with open("scores.txt", 'a') as f:
        f.write(f"Benign: {len(ben_paths)}, Malware: {len(mal_paths)} || Train: {len(x_train)}, Test: {len(x_test)}\n")
        for i in [accuracy_score, precision_score, recall_score, f1_score]:
            score = i(result, y_test)
            print(f"{i.__name__} : {score:5f}")
            f.write(f"{i.__name__} : {score:5f}\n")
    with open("./wrong_files.csv", 'w', encoding='utf-8') as f:
        f.write("hash,label\n")
        for i in range(len(files_test)):
            if result[i] != y_test[i]:
                if y_test:
                    f.write(f"{files_test[i].split(os.extsep)[0]},1\n")
                else:
                    f.write(f"{files_test[i].split(os.extsep)[0]},0\n")


if __name__ == '__main__':
    main(sys.argv)
