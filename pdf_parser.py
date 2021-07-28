import io
import multiprocessing as mp
import os
import pickle

from tqdm import tqdm

BEN_PATH = r'D:\Source\pdf\Benign_PDF'
MAL_PATH = r'D:\Source\pdf\Malicious_PDF'

MAL_OUT_BASE = r'E:\Source\pdf\mal'
BEN_OUT_BASE = r'E:\Source\pdf\ben'


def parse_pdf(file):
    ret = {
        'meta': {'file_size': 0},
        'header': {},
        'body': {'inv_obj_cnt': 0},
        'xref': {},
        'trailer': {}
    }

    if isinstance(file, io.BufferedReader):
        buffer = file.read()
    elif isinstance(file, bytes):
        buffer = file
    elif os.path.isfile(file):
        file_name = file.split(os.sep)[-1].rsplit(os.extsep, maxsplit=1)[0]
        with open(file, 'rb') as f:
            buffer = f.read()
    ret['meta']['file_size'] = len(buffer)
    buffer = buffer.replace("endobj".encode(), "endobj\r\n".encode())
    buffer = buffer.replace("\t".encode(), " ".encode())
    buffer = buffer.replace(" obj".encode(), " obj\r\n".encode())
    buffer = buffer.split('\r\n'.encode())
    data = []
    for i in buffer:
        for j in i.split('\r'.encode()):
            for k in j.split('\n'.encode()):
                data.append(k)

    head = 0
    try:
        ret['header'] = data[head].decode()
    except UnicodeDecodeError:
        ret['header'] = data[head]
    while head < len(data) and 'xref'.encode() not in data[head]:
        # try parse obj
        temp = data[head].split(" ".encode())
        if len(temp) == 3 and temp[-1] == 'obj'.encode():
            try:
                obj_num, obj_version = map(int, temp[:-1])
                ret['body'][obj_num] = {'version': obj_version, 'tags': set()}
                head += 1
                if head >= len(data):
                    break
                while head < len(data) and 'endobj'.encode() not in data[head]:
                    if 'stream'.encode() in data[head]:
                        ret['body'][obj_num]['stream'] = b''
                        head += 1
                        if head >= len(data):
                            ret['body'][obj_num]['actual_length'] = len(ret['body'][obj_num]['stream'])
                            break
                        while head < len(data) and 'endstream'.encode() not in data[head]:
                            ret['body'][obj_num]['stream'] += data[head]
                            head += 1
                            if head >= len(data):
                                break
                        ret['body'][obj_num]['actual_length'] = len(ret['body'][obj_num]['stream'])
                    if head == len(data):
                        break
                    temp = data[head].split(" ".encode())
                    if temp[0] == '/Length'.encode() and len(temp) == 2:
                        ret['body'][obj_num]['length'] = int(temp[1])
                    for i in temp:
                        for j in i.split('/'.encode()):
                            ret['body'][obj_num]['tags'].add(
                                j.decode().replace("<<", "").replace(">>", "").replace("[", "").replace("]", ""))
                    head += 1
            except ValueError:
                ret['body']['inv_obj_cnt'] += 1
        head += 1

    with open(MAL_OUT_BASE + os.sep + file_name + os.extsep + 'pickle', 'wb') as f:
        pickle.dump(ret, f)


if __name__ == '__main__':
    file_list = []
    for path, _, files in os.walk(MAL_PATH):
        for file in files:
            if os.extsep in file:
                name, ext = file.rsplit(os.extsep, maxsplit=1)
            else:
                name, ext = file, 'file',
            if ext == 'pdf' or ext == 'file':
                file_list.append(path + os.sep + file)

    with mp.Pool(processes=os.cpu_count() // 2) as pool:
        for _ in tqdm(pool.imap_unordered(parse_pdf, file_list), total=len(file_list)):
            pass
