import os
import pickle
import sys

from tqdm import tqdm

from Utils import get_file_name_ext


def main(args: list):
    file_foo = None
    model_path = None
    feature_path = []
    # Parse Arguments
    if len(args) == 3:
        _, file_foo, model_path = args
    else:
        print(f"Usage:\npython Inference.py [file directory of path] [model path]\n" +
              f"model path : shows select prompt if 'select' pass to model path")
        exit(0)

    if model_path == 'select':
        models = []
        for path, dirs, files in os.walk(os.curdir):
            for file in files:
                name, ext = get_file_name_ext(path + os.sep + file)
                if 'model_' in name and ext == 'pickle':
                    models.append((file, path + os.sep + file))
        if len(models) == 0:
            raise FileNotFoundError("No Trained Model Exists.")
        for idx in range(len(models)):
            print(f"{idx}: {models[idx][0]}")
        idx = int(input("Select model : "))
        with open(models[idx][1], 'rb') as f:
            model = pickle.load(f)

    if os.path.isfile(file_foo):
        feature_path.append(file_foo)
    else:
        for path, dirs, files in os.walk(file_foo):
            for file in files:
                name, ext = get_file_name_ext(path + os.sep + file)
                if ext == 'pickle':
                    feature_path.append(path + os.sep + file)

    # Loading Features
    dataset = [[], []]
    print("Loading features...")
    for i in tqdm(feature_path):
        name, ext = get_file_name_ext(i)
        with open(i, 'rb') as f:
            dataset[0].append(name + os.extsep + ext)
            dataset[1].append(pickle.load(f))

    result = model.predict(dataset[1])
    assert len(result) == len(dataset[0])
    # Return wrong files hash and label
    save_path = os.curdir + os.sep + "inference_result" + os.extsep + 'csv'
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write("file_name,predict\n")
        for i in range(len(result)):
            f.write(f"{dataset[0][i]},{result[i]}\n")
    print(f"Inference result saved at {save_path}")


if __name__ == '__main__':
    main(sys.argv)
