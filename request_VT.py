PATH = r"C:\Users\forgo\Desktop\lab\c\hash_list.txt"
PATH2 = r"C:\Users\forgo\Desktop\lab\c\checked_list.txt"
PATH3 = r"C:\Users\forgo\Desktop\lab\c\report"

# open file list
f = open(PATH,"r")
check = set(f.readlines())
f.close()


# open checked list
f = open(PATH2,"r")
checked = set(f.readlines())
f.close()

# generate check list
check = list(check - checked)
for i in range(len(check)):
    check[i] = check[i].strip()

#print(check)
