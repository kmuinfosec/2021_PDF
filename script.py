import os
from tqdm import tqdm
import multiprocessing as mp

os.environ['OMP_NUM_THREADS'] = '32'


def exec_command(command):
    os.system(command)


def main():
    commands = []
    for csv in [r'C:\Users\seclab\PycharmProjects\2021_PDF\Malicious_PDF.csv']:
        with open(csv, 'r') as f:
            data = f.read().split('\n')
            for file_path in tqdm(data[1:]):
                if os.extsep in file_path:
                    json_path = file_path.split(os.extsep)[0] + os.extsep + 'pdfjson'
                else:
                    json_path = file_path + os.extsep + 'pdfjson'
                ex_path = 'pdf-parser.py'
                command = "python " + ex_path + " " + file_path + " > " + json_path
                commands.append(command)
    with mp.Pool(processes=32) as pool:
        for _ in tqdm(pool.imap_unordered(exec_command, commands), total=len(commands)):
            continue


if __name__ == '__main__':
    main()
