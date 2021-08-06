import hashlib
import os
import re


PATH = r"E:\PDF\Malicious_PDF\Malicious_PDF\2017\5318eca1d568132a5aa09bd5d697ac72.vir"
#r"E:\PDF\Malicious_PDF\Malicious_PDF\2017\864ee479b3e770c2c6c7647b0c066112.vir"
#r"D:\K-lab\MalwareData\jiranjigyodata_pdf\pdf_mal\0fdb4765cbc42654d351381b7ac1c87114ba984d1d5ca500f12fc5f1b816da39.vir"


f = open(PATH, "rb")
data = f.read()
f.close()


# Header

header_start_address = data.find(b"%PDF")
header_end_address = header_start_address + 8
HEADER = data[header_start_address:header_end_address]
print(HEADER)

# Body

body_obj_start_address = []
body_obj_end_address = []

p = re.compile(b"[0-9]{1,7} [0-9]{1,7} obj", re.IGNORECASE)
m = p.finditer(data)

for match_object in m:
    body_obj_start_address.append(match_object.start())

for start_address in body_obj_start_address:
    address = data.find(b"endobj", start_address)
    body_obj_end_address.append(-1 if address -1 else address + 6)

for start, end in zip(body_obj_start_address, body_obj_end_address):
    print(data[start:end])

# Cross-Reference Table

cross_reference_table_start_address = []
cross_reference_table_end_address = []

p = re.compile(b"xref", re.IGNORECASE)
m = p.finditer(data)

for match_object in m:
    cross_reference_table_start_address.append(match_object.start())

p = re.compile(b"startxref", re.IGNORECASE)
m = p.finditer(data)

for match_object in m:
        try:
            cross_reference_table_start_address.remove(match_object.start()+5)
        except:
            pass

for start in cross_reference_table_start_address:
    address = data.find(b"trailer", start)
    address = address - 1 if address != -1 else -1
    cross_reference_table_end_address.append(address)

for start, end in zip(cross_reference_table_start_address, cross_reference_table_end_address):
    print(data[start:end])

# Trailer

trailer_start_address = []
trailer_end_address = []

p = re.compile(b"trailer", re.IGNORECASE)
m = p.finditer(data)

for match_object in m:
    trailer_start_address.append(match_object.start())


p = re.compile(b"%EOF", re.IGNORECASE)
m = p.finditer(data)

for match_object in m:
    trailer_end_address.append(match_object.end())

trailer_error_flag = False

if len(trailer_start_address) != len(trailer_end_address):
    print("different trailer keyword numbers")
else:
    for start, end in zip(trailer_start_address, trailer_end_address):
        if start > end:
            trailer_error_flag = True
            break

if not trailer_error_flag:
    for start, end in zip(trailer_start_address, trailer_end_address):
        print(data[start:end])
