import base64
import binascii
import os
import pickle
import sys
import zlib

import chardet
import networkx as nx
from matplotlib import pyplot as plt
from tqdm import tqdm

from Utils import get_entropy, get_file_name_ext

PARSE_PATH = r'E:\Source\pdf\mal_parse'


def decode_run_length(data: bytes):
    if len(data) % 2 != 1:
        output = bytes()
        for x in range(0, len(data), 2):
            length = data[x]
            value = data[x + 1: x + 2]
            output += length * value
        return output
    else:
        return data


def check(file_path):
    """
    {
    'version' : str
    'body': {
        'obj_num': {
            'tags':string, bytes
            'stream':bytes (if exist)
            'reference':string, bytes (if exist)
        }
    'xref' : string, bytes
    'trailer': tuple
    """
    with open(file_path, 'rb') as f:
        file_hash, _ = get_file_name_ext(file_path)
        parse_dict = pickle.load(f)
    ret = {
        'malicious': [],
        'suspicious': [],
        'decoded': dict()
    }
    # Extract from version
    if parse_dict['version'] == 'Invalid':
        ret['malicious'].append("Invalid PDF Version")
    elif int(parse_dict['version'].rsplit('.')[-1]) <= 3:
        ret['suspicious'].append("Vulnerable PDF Version")

    # Extract from body
    for obj_num in parse_dict['body']:
        cur_obj = parse_dict['body'][obj_num]
        if 'tags' in cur_obj:
            if '/JS' in cur_obj['tags'] or '/JavaScript' in cur_obj['tags']:
                ret['malicious'].append(f"Contains javascript at obj {obj_num}")
            if '/AA' in cur_obj['tags'] or '/OpenAction' in cur_obj['tags']:
                ret['suspicious'].append(f"Contains open action at obj {obj_num}")
            if '/EmbeddedFile' in cur_obj['tags']:
                ret['suspicious'].append(f"Contains embedded file at obj {obj_num}")
            if 'stream' in cur_obj:
                for stream in cur_obj['stream']:
                    entropy = get_entropy(stream)
                    if entropy >= 7.99:
                        ret['malicious'].append(f"High stream entropy at obj {obj_num}")
                    # enc_type = chardet.detect(stream)
                    # if enc_type['confidence'] > 0.7:
                    #     try:
                    #         decoded = stream.decode(enc_type['encoding'])
                    #         ret['decoded'][obj_num] = (enc_type['encoding'], decoded)
                    #     except Exception as e:
                    #         pass
                    if '/ASCIIHexDecode'.lower() in map(str.lower, cur_obj['tags']):
                        try:
                            decoded = binascii.unhexlify(
                                ''.join([c for c in stream.decode() if c not in ' \t\n\r']).rstrip('>'))
                            ret['decoded'][obj_num] = ('/ASCIIHexDecode', decoded)
                        except Exception as e:
                            pass
                    elif 'ASCII85Decode'.lower() in map(str.lower, cur_obj['tags']):
                        try:
                            decoded = base64.a85decode(stream)
                            ret['decoded'][obj_num] = ('ASCII85Decode', decoded)
                        except Exception as e:
                            pass
                    elif 'FlateDecode'.lower() in map(str.lower, cur_obj['tags']):
                        try:
                            decoded = zlib.decompress(stream).decode()
                            ret['decoded'][obj_num] = ('FlateDecode', decoded)
                        except Exception as e:
                            pass
                    elif 'RunLengthDecode'.lower() in map(str.lower, cur_obj['tags']):
                        try:
                            decoded = decode_run_length(stream)
                            ret['decoded'][obj_num] = ('RunLengthDecode', decoded)
                        except Exception as e:
                            pass
        if obj_num in ret['decoded']:
            if 'eval' in ret['decoded'][obj_num]:
                ret['malicious'].append(f"Eval method exists in Javascript at {obj_num}")
            if 'String.fromcharcode' in ret['decoded'][obj_num]:
                ret['malicious'].append(f"fromcharcode method exists in Javascript at {obj_num}")
            if all(i in ret['decoded'][obj_num] for i in 'spray heap app.viewerVersion getPageNthWord'.split(" ")):
                ret['malicious'].append(f"BufferOverflow method exists in Javascript at {obj_num}")
    return ret, file_hash


def build_network(file_path, save_path):
    file_hash, _ = get_file_name_ext(file_path)
    with open(file_path, 'rb') as f:
        parse_result = pickle.load(f)
    ref_network = nx.DiGraph()
    stream = []
    non_stream = []
    javascript = []
    for obj_num in parse_result['body']:
        cur_obj = parse_result['body'][obj_num]
        if 'reference' in cur_obj:
            if 'tags' in cur_obj and ('/JavaScript' in cur_obj['tags'] or '/JS' in cur_obj['tags']):
                javascript.append(obj_num)
            elif 'stream' in cur_obj and len(cur_obj['stream']) > 0:
                stream.append(obj_num)
            else:
                non_stream.append(obj_num)

            ref_network.add_node(obj_num)
            references = cur_obj['reference']
            for ref in references:
                ref_num = ref.split(' ')[0]
                ref_network.add_edge(obj_num, ref_num)

    plt.figure(figsize=(25, 25))
    plt.title(f"Reference Network of {file_hash}")
    pos = nx.kamada_kawai_layout(ref_network)
    nx.draw_networkx_edges(ref_network, pos)
    nx.draw_networkx_labels(ref_network, pos)
    nx.draw_networkx_nodes(ref_network, pos, nodelist=non_stream, node_color='#34c6eb', label='Non-Stream')
    nx.draw_networkx_nodes(ref_network, pos, nodelist=stream, node_color='#ff9d00', label='Stream')
    nx.draw_networkx_nodes(ref_network, pos, nodelist=javascript, node_color='#ff0505', label='JavaScript')
    plt.legend()
    plt.savefig(save_path)
    plt.close()
    return ref_network


def main(args):
    file_path = []
    file_foo = None
    out_dir = "./"
    graph = False
    if len(args) == 4:
        _, file_foo, out_dir, graph, = args
    elif len(args) == 3:
        _, file_foo, out_dir = args
    else:
        print("Usage:\npython Analyzer.py [parsed file path or directory] [output path] [graph=False]")
        file_foo = r"E:\Source\pdf\ben_parse"
        out_dir = "./"
    if os.path.isfile(file_foo):
        file_path.append(file_foo)
    else:
        for path, _, files in os.walk(file_foo):
            for file in files:
                file_path.append(path + os.sep + file)
    for file in tqdm(file_path):
        result, name = check(file)
        with open(out_dir + os.sep + name + os.extsep + 'pickle', 'wb') as f:
            pickle.dump(result, f)
        if graph:
            build_network(file, out_dir)


if __name__ == '__main__':
    main(sys.argv)
