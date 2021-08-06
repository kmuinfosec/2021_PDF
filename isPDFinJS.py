import os
import re
import sys


def checkPDFsignature(file_data):
    """
    :param file_data: entire file data or file's first line data
    :return: boolean
    if the file type is PDF return true
    """
    if file_data[:4] == b"%PDF":
        return True
    else:
        return False

def checkPDFinJS(file_data):
    """
    :param file_data: entire file data
    :return: boolean
    search JS, JavaScript Keyword in entire PDF File
    """
    p = re.compile(b"/JavaScript", re.IGNORECASE)
    if len(p.findall(file_data)) >= 1:
        return True

    p = re.compile(b"/JS", re.IGNORECASE)
    if len(p.findall(file_data)) >= 1:
        return True
    return False

PATH = [
    r"D:\K-lab\MalwareData\Malicious_PDF\Malicious_PDF\2017",
    r"D:\K-lab\MalwareData\Malicious_PDF\Malicious_PDF\2018",
    r"D:\K-lab\MalwareData\Malicious_PDF\Malicious_PDF\2019"
]

for p in PATH:
    for file_name in os.listdir(p):
        if os.path.isdir(os.path.join(p,file_name)) == False:
            f = open(os.path.join(p,file_name),"rb")
            d = f.read()
            f.close()

            if checkPDFsignature(d) == True:
                if checkPDFinJS(d) == True:
                    print(file_name) 