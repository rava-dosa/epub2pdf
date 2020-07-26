from bs4 import BeautifulSoup
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
from os import listdir
import sys
import shutil
import zipfile
global_root_dir=""
filename=""
def read_css():
    font_config = FontConfiguration()
    ret=[]
    l=listdir(global_root_dir+"css")
    for x in l:
        ret.append(global_root_dir+"css/"+x)
    return ret

def writepdf(file_data):
    font_config=FontConfiguration()
    css=read_css()
    html=HTML(string=file_data)
    # print(css)
    html.write_pdf(filename+'.pdf', stylesheets=css,font_config=font_config)

def generatepdf():
    f=open(global_root_dir+"temp.xhtml","w")
    with open (global_root_dir+"toc.ncx", "r") as myfile:
        data=myfile.read()
    soup = BeautifulSoup(data, 'html.parser')
    l=soup.find_all("content")
    prev=""
    for x in l:
        temp=x.get("src")
        temp1=temp.split("#")[0]
        if(prev==temp1):
            continue
        else:
            with open (global_root_dir+ temp1, "r") as xhtml_epub:
                xhtml_data=xhtml_epub.read()
                f.write(xhtml_data)
        prev=temp1
    f.close()
    f=open(global_root_dir+"temp.xhtml","r")
    writepdf(f.read())
def extract_zip_to_temp(path):
    with zipfile.ZipFile(path, 'r') as zip_ref:
        ret=zip_ref.extractall("/tmp/epub_temp/")
        print(ret)
if __name__ == "__main__": 
    unzip_file_path=sys.argv[1]
    filename=unzip_file_path.split("/")[-1]
    print(filename)
    last4=filename[-4:]
    if(last4!="epub"):
        print("It's a {} file".format(last4))
        quit()
    shutil.copy(unzip_file_path,"/tmp/epub_temp.zip")
    extract_zip_to_temp("/tmp/epub_temp.zip")
    global_root_dir="/tmp/epub_temp/OEBPS/"
    # print(unzip_file_path)
    filename=filename[:-4]
    generatepdf()