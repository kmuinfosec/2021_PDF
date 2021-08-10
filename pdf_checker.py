import os
import re

BASE_PATH = r'D:\Source\pdf\Benign_PDF'


def is_pdf(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    if re.match(rb'%PDF-', data) is None:
        os.remove(file_path)


def main():
    for path, dirs, files in os.walk(BASE_PATH):
        for file in files:
            if os.extsep in file:
                name, ext = file.split(os.extsep)
            else:
                name, ext = file, 'file',
            if ext == 'file' or ext == 'pdf':
                is_pdf(path + os.sep + file)
            else:
                os.remove(path + os.sep + file)


if __name__ == '__main__':
    main()
