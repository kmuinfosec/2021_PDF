import multiprocessing as mp
import os
import pickle
import re
import sys

from tqdm import tqdm

from Utils import get_file_name_ext


def star(args):
    return parse_pdf(*args)


def parse_pdf(file_path, save_path):
    ret = dict()
    with open(file_path, 'rb') as f:
        data = f.read()
    # Parse Metadata
    ret['file_size'] = os.path.getsize(file_path)

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
        obj_tags_1 = set(map(bytes.decode, re.findall(rb'(/\w+)[^>]', obj_dict)))
        obj_tags_2 = set(map(bytes.decode, re.findall(rb'(/\w+)>{2}', obj_dict)))
        ret['body'][obj_id]['tags'] = obj_tags_1.union(obj_tags_2)
        obj_refer = list(map(bytes.decode, re.findall(rb'\d+\s+\d+\sR', obj_dict)))
        if len(obj_refer) != 0:
            ret['body'][obj_id]['reference'] = obj_refer
        streams = re.findall(rb'stream\s*?([\s\S]*?)\s*?endstream', obj_string, re.IGNORECASE | re.MULTILINE)
        if len(streams) != 0:
            ret['body'][obj_id]['stream'] = streams

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
                for i in ref_table:
                    try:
                        ret['xref'][ref_num].append(i.decode())
                    except UnicodeDecodeError:
                        ret['xref'][ref_num].append(i)

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
                try:
                    ret['trailer'][idx].add((tag.decode(), value.decode().rstrip()))
                    if tag in ret['trailer'][idx]:
                        ret['trailer'][idx].remove(tag)
                except UnicodeDecodeError:
                    ret['trailer'][idx].add((tag, value.rstrip()))
                    if tag in ret['trailer'][idx]:
                        ret['trailer'][idx].remove(tag)

    with open(save_path, 'wb') as f:
        pickle.dump(ret, f)
    return ret


def pretty_print(parse_result: dict):
    print("PDF")
    for key in parse_result:
        if key == 'file_size':
            print(f"└file size -> {parse_result[key]}")
        if key == 'version':
            print(f"└version -> {parse_result[key]}")
        elif key == 'body':
            print(f"└body")
            for ref_num in parse_result[key]:
                print(f'\t└Obj {ref_num}')
                if 'stream' in parse_result[key][ref_num]:
                    print("\t\t└Contains Stream")
                if 'reference' in parse_result[key][ref_num]:
                    referencing = parse_result[key][ref_num]['reference']
                    print(f'\t\t└Referencing: {referencing}')
                for i in parse_result[key][ref_num]:
                    if i == 'tags':
                        print("\t\t└tags")
                        for tag in parse_result[key][ref_num][i]:
                            print(f"\t\t\t└{tag}")
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


def main(args: list):
    if len(args) != 4:
        print("Usage:\npython PDF_ParserV2.py [raw file directory] [output directory] [cpu assign]")
    else:
        _, raw_dir, save_dir, cpu_count = args
        cpu_count = int(cpu_count)
        mp.freeze_support()
        raw_path = []
        save_path = []
        for path, _, files in os.walk(raw_dir):
            for file in files:
                name, ext = get_file_name_ext(path + os.sep + file)
                if ext == 'pdf' or ext == 'vir':
                    raw_path.append(path + os.sep + file)
                    save_path.append(save_dir + os.sep + name + os.extsep + 'pickle')
        if cpu_count > 1:
            with mp.Pool(processes=cpu_count) as pool:
                total = len(raw_path)
                chunk_size = min(total // cpu_count // 2, 256)
                for _ in tqdm(pool.imap_unordered(star, zip(raw_path, save_path), chunksize=chunk_size), total=total):
                    continue
                pool.close()
                pool.join()
        else:
            for path in tqdm(zip(raw_path, save_path)):
                parse_pdf(*path)


if __name__ == '__main__':
    main(sys.argv)
