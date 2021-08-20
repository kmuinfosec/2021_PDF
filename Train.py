import os
import pickle
import sys

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from Utils import now


def main(args: list):
    # Parse Arguments
    ben_dir = None
    mal_dir = None
    test_size = 0.3
    if len(args) == 3:
        _, ben_dir, mal_dir = args
    elif len(args) == 4:
        _, ben_dir, mal_dir, test_size = args
        test_size = float(test_size)
    else:
        print(f"Usage:\npython Train.py [benign features directory] [malware features directory] [test size=0.3]")
        exit(0)
    assert ben_dir is not None and mal_dir is not None

    # Loading Features
    print("Loading features...")
    labels = []
    features = []
    file_names = []
    ben_paths = []
    mal_paths = []
    for label, base in enumerate([ben_dir, mal_dir]):
        for file in os.listdir(base):
            if label:
                mal_paths.append(base + os.sep + file)
            else:
                ben_paths.append(base + os.sep + file)
    for label, base in enumerate([ben_paths, mal_paths]):
        postfix = 'malware' if label else 'benign'
        for i in tqdm(base, postfix=postfix):
            name = i.split(os.sep)[-1].split(os.extsep)[0]
            with open(i, 'rb') as f:
                features.append(pickle.load(f))
                labels.append(label)
                file_names.append(name)
    print(f"Benign: {len(ben_paths)}, Malware: {len(mal_paths)} are used")
    f_train, f_test, x_train, x_test, y_train, y_test = train_test_split(file_names, features, labels,
                                                                         test_size=test_size, random_state=486)
    assert len(f_train) == len(x_train) == len(y_train)

    # Training Model
    model = RandomForestClassifier(n_jobs=16, random_state=486)
    print("Training model...")
    model.fit(x_train, y_train)
    save_path = f"{os.curdir}{os.sep}model_{now()}{os.extsep}pickle"
    with open(save_path, 'wb') as f:
        pickle.dump(model, f)
        print(f"Model saved at {save_path}")

    # Evaluate Model
    print("\nEvaluating model...")
    result = model.predict(x_test)
    print("\nScore")
    for i in [accuracy_score, precision_score, recall_score, f1_score]:
        score = i(result, y_test)
        print(f"{i.__name__} : {score:5f}")

    # Return wrong files hash and label
    with open(f"{os.curdir}{os.sep}wrong_files{os.extsep}csv", 'w', encoding='utf-8') as f:
        f.write("name,label,predict\n")
        for i in range(len(f_test)):
            if result[i] != y_test[i]:
                f.write(f"{f_test[i].split(os.extsep)[0]},{y_test[i]},{result[i]}\n")


if __name__ == '__main__':
    main(sys.argv)
