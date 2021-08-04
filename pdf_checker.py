import multiprocessing as mp
import os
import pickle
import re

from tqdm import tqdm

BEN_BASE = r'D:\pdf\ben'
MAL_BASE = r'D:\pdf\pdf2021'

JS_SET = set()
PDF_SET = set()


def find(path):
    re_js1 = re.compile(rb'(<<).*(/JavaScript)+.*(>>)', re.IGNORECASE)
    re_js2 = re.compile(rb'(<<).*(/JS)+.*(>>)', re.IGNORECASE)
    hash_ = path.split(os.sep)[-1].rsplit(os.extsep, maxsplit=1)[0]
    assert len(hash_) == len('00003a0fae3666372922a584b6c2ac1d')
    with open(path, 'rb') as f:
        data = f.read()
        temp = data[:100]
        pdf_idx = temp.find("%PDF".encode())
        if pdf_idx == 0:
            if (re_js1.search(data) is not None) or (re_js2.search(data) is not None):
                return 3, hash_
            else:
                return 2, hash_
        else:
            return 1, hash_


def main():
    paths = []
    for base in [BEN_BASE, MAL_BASE]:
        for path, dirs, files in os.walk(base):
            for file in files:
                if os.extsep in file:
                    name, ext = file.rsplit(os.extsep, maxsplit=1)
                else:
                    name, ext = file, "file",
                if ext == 'vir' or ext == 'pdf':
                    paths.append(path + os.sep + file)
    with mp.Pool(processes=int(os.cpu_count() * 0.8)) as pool:
        for ret, hash_ in tqdm(pool.imap_unordered(find, paths), total=len(paths)):
            if ret == 3:
                PDF_SET.add(hash_)
                JS_SET.add(hash_)
            elif ret == 2:
                PDF_SET.add(hash_)
            else:
                pass
        pool.close()
        pool.join()
    with open('./js_container', 'wb') as f:
        pickle.dump(JS_SET)
    with open('./pdf_container', 'wb') as f:
        pickle.dump(PDF_SET)


if __name__ == '__main__':
    mp.freeze_support()
    main()
