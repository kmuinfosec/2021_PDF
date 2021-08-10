import re
import multiprocessing as mp
import os
from tqdm import tqdm

RAW_PATH = r'D:\Source\pdf\Benign_PDF'
PARSE_PATH = r''
MP = True


def parse_pdf(file_path):
    ret = dict()
    with open(file_path, 'rb') as f:
        data = f.read()
        version = re.search(rb'%PDF-\d\.\d', data, re.IGNORECASE)
        if version is not None:
            version = version.group(0).decode()
            if re.search(r'\d+\.\d+', version):
                ret['version'] = version
            else:
                ret['version'] = 'Invalid'
        else:
            ret['version'] = 'Invalid'

        ret['body'] = dict()
        objs = re.findall(rb'\d+\s\d\sobj+[\s\S]*?endobj', data, re.IGNORECASE | re.MULTILINE)
        for i in objs:
            obj_id, obj_version = re.split(rb"\s", re.search(rb'(\d+\s\d+)\s*?obj', i).group(1))
            for obj_dict in re.findall(rb'<<[\s\S]*>>', i, re.IGNORECASE | re.MULTILINE):
                ret['body'][obj_id] = dict()
                ret['body'][obj_id]['tags'] = set(re.findall(rb'/\w+', obj_dict))
                tags_with_value = re.findall(rb"(/\w+)([^/]+)", obj_dict, re.IGNORECASE | re.MULTILINE)
                for tag, value in tags_with_value:
                    if tag + value not in ret['body'][obj_id]['tags']:
                        ret['body'][obj_id]['tags'].add((tag, value))
                        if tag in ret['body'][obj_id]['tags']:
                            ret['body'][obj_id]['tags'].remove(tag)
            streams = re.findall(rb'stream(\s*?[\s\S]*?\s*?)endstream', i, re.IGNORECASE | re.MULTILINE)
            if streams:
                ret['body'][obj_id]['stream'] = []
                for stream in streams:
                    ret['body'][obj_id]['stream'].append(stream)

        xref_tables = re.findall(rb'xref\s+[\s\S]*?trailer', data, re.IGNORECASE | re.MULTILINE)
        ret['xref'] = dict()
        if len(xref_tables):
            for table in xref_tables:
                ref_num = re.search(rb'xref[\s\S]*?(\d)+\s(\d+)', table).group(2)
                ref_table = re.findall(rb'\d+\s\d+\s\S', table)
                ret['xref'][ref_num] = []
                for i in ref_table:
                    ret['xref'][ref_num].append(i)

        ret['trailer'] = dict()
        trailers = re.findall(rb'trailer[\s\S]*?<<([\s\S]*?)>>[\s\S]*?startxref', data, re.IGNORECASE | re.MULTILINE)
        for idx, trailer in enumerate(trailers):
            ret['trailer'][idx] = dict()
            ret['trailer'][idx] = set(re.findall(rb'/\w+', trailer))
            tags_with_value = re.findall(rb"(/\w+)([^/]+)", trailer, re.IGNORECASE | re.MULTILINE)
            for tag, value in tags_with_value:
                if tag + value not in ret['trailer'][idx]:
                    ret['trailer'][idx].add((tag, value))
                    if tag in ret['trailer'][idx]:
                        ret['trailer'][idx].remove(tag)
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
            if ext == 'file' or ext == 'pdf':
                paths.append(path + os.sep + file)
    if MP:
        with mp.Pool(processes=os.cpu_count() // 2) as pool:
            total = len(paths)
            chunk_size = total // os.cpu_count() // 8
            for _ in tqdm(pool.imap_unordered(parse_pdf, paths, chunksize=chunk_size), total=total):
                continue
    else:
        for path in tqdm(paths):
            result = parse_pdf(path)


if __name__ == '__main__':
    main()
