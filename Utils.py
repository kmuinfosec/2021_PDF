import collections
import datetime
import math
import os


def get_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    occurrences = collections.Counter(data)
    entropy = 0
    for x in occurrences.values():
        p_x = float(x) / len(data)
        entropy -= p_x * math.log(p_x, 2)
    return entropy


def get_file_name_ext(absolute_path: str) -> tuple:
    temp = absolute_path.split(os.sep)
    if os.extsep in temp[-1]:
        name, ext = temp[-1].rsplit(os.extsep, maxsplit=1)
    else:
        name, ext = temp[-1], 'file'
    return name, ext


def now():
    return "".join(map(str, datetime.datetime.today().timetuple()[:5]))
