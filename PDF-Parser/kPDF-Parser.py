import io
import os



def parse_pdf(file_path):
    ret = {
        'meta': {'file_size': 0},
        'header': {},
        'body': {'inv_obj_cnt': 0},
        'xref': {},
        'trailer': {}
    }
    if os.path.isfile(file_path):
        file_name = file_path.split(os.sep)[-1].rsplit(os.extsep, maxsplit=1)[0]
        with open(file_path, 'rb') as f:
            buffer = f.read()
    else:
        print("Invalid File or Filename")
        return
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

    return ret

PATH = r"E:\PDF\mal\0902293f19286270122eacba8bf74c49.vir"
result = parse_pdf(PATH)

print(result)