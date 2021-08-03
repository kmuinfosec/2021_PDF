PATH = r"C:\Users\forgo\Desktop\lab\c\file_list.txt"
PATH2 = r"C:\Users\forgo\Desktop\lab\c\hash_list.txt"

f = open(PATH,"r")
data = f.readlines()
f.close()

f = open(PATH2, "w")

for d in data:
    f.write(d.split(" ")[-1].split("_")[-1])

f.close()

