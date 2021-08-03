import time
import vtapi3
import sys

PATH = r"C:\Users\forgo\Desktop\lab\hash_list.txt"
PATH2 = r"C:\Users\forgo\Desktop\lab\checked_list.txt"
PATH3 = "C:\\Users\\forgo\\Desktop\\lab\\report\\"

VT_API_KEY = ["0310e1ca827d81cc0f6b3aff5d8f03ec3e8c505993f5ff83c1a3682f6dfee130",
"839d9ca5c54b56584d295ca75c43a98e30daf00dd3c7eb90099880a61f85c15a",
"82296d0b5baa9ed0c29a77df6ac7446d746c76aca596ccb2ad3a3fa7f13c2d95",
"f2de233b20d028078c52f9186800f79ba6ecc5a6744e020461a394dd69b427b1",
"9fc31736b88fe6df5de362cdda1c9451c4cab87ebb69b0c9b4159618ca230c24",
"aaf0fa5d4ce22952a5bf18c551e7eab33a4782159a81ceaa01c55f751b6cf152",
"1669f7ba220cf3cfe75008fd5ac8fa9634c2a1723a2be770c86506430fd3ad0e",
"cd21d484f92c7a030cfe8857564618f3427832af509f351574920c8a28e9f23f",
"e4b420a38956d5a8cf81c4e592ec23d4679fad165a676785a3af2a68a9de6647",
"41f10e7915d816930536c553c36f162e14f1192d8d0aaa6fbd20ea23f982099f",
"3cf47a6b5bec265b70687b5c2640051fd9560a6f44a72ea3b66e1de68f21202b",
"676eede02431655d7dd05f36f1b093e7ca146279a9fc6d1704c93ddd8afcb43c",
"6e951dc386e21a2babb31ad6b06f7cd399b0bc1333c736f1b4ba96a6607d00fb",
"60b1194a18ae146a5a2d58d9c222b9e1f0995d58136a168f5d4be3de92882522",
"cd83be8f0a91c0394639495505738f5f6800c4888c78c1bae92f63bc5efb2971",
"0b5a470d49af4c60c1da97394d1c985b202d9deaada40e7f8d796f97ae666892",
"82f5d5572700e0d3682a0ad9ee3fa01319ec3d1ccfe9be4f472d92296fa43fa1",
"3f02771482036a25b503051e7c62e11a3d419f6203021d93428077cfa7587e43",
"d56cc8ca98268ad4d657eebb19b3d06fc563a290293f5843805c2f2b6edf0e20",
"d4a812bff6b9c01f74fb832d671290106ad1e9ef2c613b76a5f0f86a0c5b6fb1",
"d577769853ddc153085a63ea249cff9eac129f432adfad96dd2c82f14b44a473",
"d4f33b0aba1ff10fa6a27e854775c52844ba88fa41a84324d62e357999d9c8fe"]

MAX_COUNT = len(VT_API_KEY) * 500

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

#print(check)

count = 0

# VT request and save requested file to list
f2 = open(PATH2, "a")
for i in range(MAX_COUNT):
    try:
        vt_files = vtapi3.VirusTotalAPIFiles(VT_API_KEY[i % len(VT_API_KEY)])
        js = vt_files.get_report(check[i])
    except vtapi3.VirusTotalAPIError as err:
        print(check[i].strip(), VT_API_KEY[i % len(VT_API_KEY)], err.err_code)
        count += 1
    else:
        if vt_files.get_last_http_error() == vt_files.HTTP_OK:
            f = open(PATH3 + check[i].strip(), "wb")
            f.write(js)
            f.close()
        else:
            print(check[i].strip(), VT_API_KEY[i % len(VT_API_KEY)], str(vt_files.get_last_http_error()))
        count += 1
        f2.write(check[i])
    if(count == MAX_COUNT):
        f2.close()
        sys.exit(0)
    if(count % len(VT_API_KEY) == 0):
        time.sleep(16)


