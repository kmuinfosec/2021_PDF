from ftplib import FTP

HOST = "203.246.112.137"
PORT = 50000
USER = "seclab_lab"
PASS = "seclab4680!"
PATH = "/vir/pe/"

ftp = FTP()
ftp.connect(HOST, PORT)
ftp.login(USER, PASS)
ftp.dir(PATH)

ftp.close()
