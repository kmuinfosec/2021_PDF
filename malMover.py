import os
import shutil
import re
import tqdm


def is_pdf_file(file_data):
    if file_data.find(b'%PDF') > -1:
        return True
    else:
        return False


def is_pdf_in_js(file_data):
    p = re.compile(b"/JS", re.IGNORECASE)
    if len(p.findall(file_data)) > 0:
        return True

    p = re.compile(b"/JavaScript", re.IGNORECASE)
    if len(p.findall(file_data)) > 0:
        return True

    return False


PATH = r"E:\PDF\benign"
PATH2 = r"E:\PDF\benign_js"


for file_name in tqdm.tqdm(os.listdir(PATH)):
    f = open(os.path.join(PATH, file_name), "rb")
    d = f.read()
    f.close()
    if is_pdf_file(d):
        if is_pdf_in_js(d):
            shutil.copy(os.path.join(PATH, file_name), os.path.join(PATH2, file_name))