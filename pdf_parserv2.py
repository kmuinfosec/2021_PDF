import pickle
import multiprocessing as mp
import os
import re

from tqdm import tqdm

RAW_PATH = r'C:\Users\FURO\Desktop\Scores'
PARSE_PATH = r'./'
MP = False
SAVE = False


def parse_pdf(file_path):
    print('-' * 25 + file_path + '-' * 25)
    file_name = file_path.split(os.sep)[-1]
    if os.extsep in file_name:
        file_hash = file_name.rsplit(os.extsep, maxsplit=1)[0]
    else:
        file_hash = file_name
    # assert len(file_hash) == len('03c7c0ace395d80182db07ae2c30f034')

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
    objs = re.findall(rb'(\d+[\s\r]\d+[\s\r]?)obj([\s\S]*?)endobj', data, re.IGNORECASE | re.MULTILINE)
    for obj_meta, obj_string in objs:
        obj_id, obj_version = map(bytes.decode, re.split(rb'\s', obj_meta, maxsplit=1, flags=re.IGNORECASE))
        ret['body'][obj_id] = {
            'version': -1,
            'tags': set(),
            'reference': [],
            'stream': []
        }
        stack = 1
        start_idx = obj_string.find(b"<<") + len(b"<<")
        end_idx = len(obj_string) - 1
        for i in range(start_idx, end_idx + 1):
            if obj_string[i:i + 2] == b'<<':
                stack += 1
            elif obj_string[i:i + 2] == b'>>':
                stack -= 1
            if stack == 0:
                end_idx = i
                break
        obj_dict = obj_string[start_idx:end_idx]
        obj_tags = set(map(bytes.decode, re.findall(rb'/\w+', obj_dict)))
        ret['body'][obj_id]['tags'] = obj_tags
        obj_refer = list(map(bytes.decode, re.findall(rb'\d+\s+\d+\sR', obj_dict)))
        ret['body'][obj_id]['reference'] = obj_refer
        streams = re.findall(rb'stream(\s*?[\s\S]*?\s*?)endstream', obj_string, re.IGNORECASE | re.MULTILINE)
        if len(streams) == 1:
            ret['body'][obj_id]['stream'].append(streams[0])

    # Parse Cross Reference Table
    xref_tables = re.findall(rb'xref\s+[\s\S]*?trailer', data, re.IGNORECASE | re.MULTILINE)
    ret['xref'] = dict()
    if len(xref_tables):
        for table in xref_tables:
            ref_meta = re.search(rb'xref[\s\S]*?(\d)+\s(\d+)', table)
            if ref_meta:
                ref_num = re.search(rb'xref[\s\S]*?(\d)+\s(\d+)', table).group(2)
                ref_table = re.findall(rb'\d+\s\d+\s\S', table)
                ret['xref'][ref_num] = list(map(bytes.decode, ref_table))

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
                ret['trailer'][idx].add((tag.decode(), value.decode().rstrip()))
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
                        print('\t└' + f"obj {ref_num} {i}")
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
    if MP:
        with mp.Pool(processes=os.cpu_count() // 2) as pool:
            total = len(paths)
            chunk_size = total // os.cpu_count() // 8
            for _ in tqdm(pool.imap_unordered(parse_pdf, paths, chunksize=chunk_size), total=total):
                continue
    else:
        for path in tqdm(paths):
            pretty_print(parse_pdf(path))


if __name__ == '__main__':
    main()
