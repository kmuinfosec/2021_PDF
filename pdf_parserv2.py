import pickle
import re
import multiprocessing as mp
import os
from tqdm import tqdm

RAW_PATH = r'D:\Source\pdf_fortrans\pdf2021'
PARSE_PATH = r'E:\Source\pdf\mal_parse'
MP = False
SAVE = False


def parse_pdf(file_path):
    file_name = file_path.split(os.sep)[-1]
    if os.extsep in file_name:
        file_hash = file_name.rsplit(os.extsep, maxsplit=1)[0]
    else:
        file_hash = file_name
    assert len(file_hash) == len('03c7c0ace395d80182db07ae2c30f034')

    ret = dict()
    with open(file_path, 'rb') as f:
        data = f.read()
    # Parse Version
    version = re.search(rb'%PDF-\d\.\d', data, re.IGNORECASE)
    if version is not None:
        version = version.group(0).decode()
        if re.search(r'\d+\.\d+', version):
            ret['version'] = version
        else:
            ret['version'] = 'Invalid'
    else:
        ret['version'] = 'Invalid'

    # Parse Body
    ret['body'] = dict()
    objs = re.findall(rb'\d+\s\d\sobj[\s\S]*?endobj', data, re.IGNORECASE | re.MULTILINE)
    for obj_string in objs:
        obj_meta = re.search(rb'(\d+\s\d+)\s*?obj', obj_string, re.IGNORECASE | re.MULTILINE).group(1)
        obj_id, obj_version = map(bytes.decode, re.split(rb"\s", obj_meta))
        ret['body'][obj_id] = dict()
        ret['body'][obj_id]['tags'] = set()
        for obj_dict in re.findall(rb'<<([\s\S]*)>>', obj_string, re.IGNORECASE | re.MULTILINE):
            obj_dict = obj_dict
            temp = re.split(rb'\s', obj_dict)
            tag = None
            parentheses = [b'[', b']', b'(', b')', b'<<', b'>>']
            idx = 0
            while idx < len(temp):
                if len(temp[idx]) != 0:
                    if idx < len(temp) and temp[idx][0] == '/':
                        tag = temp[idx]
                        if idx < len(temp) - 1 and temp[idx + 1][0] in parentheses:
                            idx += 1
                            value = []
                            while idx < len(temp) and temp[idx][-1] not in parentheses:
                                value.append(temp[idx])
                                idx += 1
                            else:
                                value.append(temp[idx])
                            print(tag, " ".join(value))
                        elif idx < len(temp) - 1 and temp[idx + 1][0] != '/':
                            idx += 1
                            value = []
                            while idx < len(temp) and temp[idx][0] != '/':
                                value.append(temp[idx])
                                idx += 1
                            print(tag, " ".join(value))
                        else:
                            print(tag)
                            idx += 1
                    else:
                        idx += 1
                else:
                    idx += 1

        streams = re.findall(rb'stream(\s*?[\s\S]*?\s*?)endstream', obj_string, re.IGNORECASE | re.MULTILINE)
        if streams:
            ret['body'][obj_id]['stream'] = []
            for stream in streams:
                ret['body'][obj_id]['stream'].append(stream)

    # Parse Cross Reference Table
    xref_tables = re.findall(rb'xref\s+[\s\S]*?trailer', data, re.IGNORECASE | re.MULTILINE)
    ret['xref'] = dict()
    if len(xref_tables):
        for table in xref_tables:
            ref_meta = re.search(rb'xref[\s\S]*?(\d)+\s(\d+)', table)
            if ref_meta:
                ref_num = re.search(rb'xref[\s\S]*?(\d)+\s(\d+)', table).group(2)
                ref_table = re.findall(rb'\d+\s\d+\s\S', table)
                ret['xref'][ref_num] = []
                for obj_string in ref_table:
                    ret['xref'][ref_num].append(obj_string)

    # Parse Trailer
    ret['trailer'] = dict()
    trailers = re.findall(rb'trailer[\s\S]*?<<([\s\S]*?)>>[\s\S]*?startxref', data,
                          re.IGNORECASE | re.MULTILINE)
    for idx, trailer in enumerate(trailers):
        ret['trailer'][idx] = dict()
        ret['trailer'][idx] = set(re.findall(rb'/\w+', trailer))
        tags_with_value = re.findall(rb"(/\w+)([^/]+)", trailer, re.IGNORECASE | re.MULTILINE)
        for tag, value in tags_with_value:
            if tag + value not in ret['trailer'][idx]:
                ret['trailer'][idx].add((tag, value))
                if tag in ret['trailer'][idx]:
                    ret['trailer'][idx].remove(tag)

    if SAVE:
        with open(PARSE_PATH + os.sep + file_hash + os.extsep + 'pickle', 'wb') as f:
            pickle.dump(ret, f)
    return ret


def pretty_print(parse_result: dict):
    print("PDF")
    for key in parse_result:
        if key == '└version':
            print(f"version -> {parse_result[key]}")
        elif key == 'body':
            print(f"└body")
            for ref_num in parse_result[key]:
                for i in parse_result[key][ref_num]:
                    if i == 'tags':
                        print('\t└' + i)
                        for tag in parse_result[key][ref_num][i]:
                            print(f"\t\t└{tag}")
        elif key == 'xref':
            print(f"└xref")
            for ref_num in parse_result[key]:
                print(f"\t└{ref_num}")
                for i in parse_result[key][ref_num]:
                    print('\t\t└', i)
        elif key == 'trailer':
            print(f"└trailer")
            for ref_num in parse_result[key]:
                for i in parse_result[key][ref_num]:
                    print(f"\t\t└{i}")


def main():
    paths = []
    for path, _, files in os.walk(RAW_PATH):
        for file in files:
            if os.extsep in file:
                name, ext = file.rsplit(os.extsep, maxsplit=1)
            else:
                name, ext = file, 'file',
            if ext == 'file' or ext == 'pdf' or ext == 'vir':
                paths.append(path + os.sep + file)
    # paths = [r'D:\Source\pdf_fortrans\pdf2021\04c9f9f06af6f06e11cd5017098d822b.vir']
    if MP:
        with mp.Pool(processes=os.cpu_count() // 2) as pool:
            total = len(paths)
            chunk_size = total // os.cpu_count() // 8
            for _ in tqdm(pool.imap_unordered(parse_pdf, paths, chunksize=chunk_size), total=total):
                continue
    else:
        for path in tqdm(paths):
            parse_pdf(path)


if __name__ == '__main__':
    main()
