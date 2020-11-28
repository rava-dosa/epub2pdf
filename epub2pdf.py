from bs4 import BeautifulSoup
from weasyprint import HTML, CSS, default_url_fetcher
from weasyprint.fonts import FontConfiguration
from os import listdir
import sys
import shutil
import zipfile
import os
from inspect import currentframe, getframeinfo
import logging
logger = logging.getLogger('weasyprint')
logger.addHandler(logging.FileHandler('/tmp/weasyprint.log'))
global_root_dir=""
filename=""
opf_name=""
image_base=""
def image_base_url():
    global global_root_dir, image_base
    global opf_name
    font_config = FontConfiguration()
    ret=[]
    f=open(global_root_dir+opf_name,"r")
    soup = BeautifulSoup(f.read(), 'lxml')
    a=soup.find("manifest")
    try:
        img_jpg=a.find("item",{"media-type":"image/jpeg"}).get("href")
        image_base=global_root_dir+img_jpg.split("/")[0]+"/"
    except:
        print("no jpeg")
    try:
        img_png=a.find("item",{"media-type":"image/png"}).get("href")
        image_base=global_root_dir+img_png.split("/")[0]+"/"
    except:
        print("no png")
    
def read_css():
    global global_root_dir
    global opf_name
    font_config = FontConfiguration()
    ret=[]
    f=open(global_root_dir+opf_name,"r")
    soup = BeautifulSoup(f.read(), 'lxml')
    a=soup.find("manifest")
    css_file=a.find("item",{"media-type":"text/css"}).get("href")
    if(css_file is None):
        print("Css not found")
    else:
        ret.append(global_root_dir+css_file)
    return ret

def get_ncx():
    global global_root_dir
    global opf_name
    f=open(global_root_dir+"META-INF/"+"container.xml", "r")
    data=f.read()
    soup = BeautifulSoup(data, 'html.parser')
    l=soup.find_all("rootfile")
    if(len(l)==0):
        print("no rootfile found")
        quit()
    else:
        l1=l[0]
        pathx=l1.get("full-path")
        if("/" in pathx):
            splitx=pathx.split("/")
            global_root_dir= global_root_dir+splitx[0]+"/"
            opf_name=splitx[1]
            f=open(global_root_dir+splitx[1],"r")
            soup = BeautifulSoup(f.read(), 'lxml')
            a=soup.find("manifest")
            ncx_file=a.find(id="ncx").get("href")
            if(ncx_file is None):
                print("NCX file not found")
                quit()
            f=open(global_root_dir+ncx_file,"r")
            return f.read()
        else:
            opf_name=pathx
            f=open(global_root_dir+pathx,"r")
            soup = BeautifulSoup(f.read(), 'lxml')
            a=soup.find("manifest")
            ncx_file=a.find(id="ncx").get("href")
            if(ncx_file is None):
                print("NCX file not found")
                quit()
            f=open(global_root_dir+ncx_file,"r")
            return f.read()
        
def writepdf(file_data):
    global global_root_dir,image_base
    font_config=FontConfiguration()
    css=read_css()
    image_base_url()
    html=HTML(string=file_data,base_url=image_base,encoding="utf8")
    # print(css)
    html.write_pdf(filename+'.pdf', stylesheets=css,font_config=font_config)

def generatepdf():
    global global_root_dir
    data=get_ncx()
    f=open(global_root_dir+"temp.xhtml","w")
    # try:
    #     with open (global_root_dir+"toc.ncx", "r") as myfile:
    #         data=myfile.read()
    # except:
    #     frameinfo = getframeinfo(currentframe())
    #     print("NCX file not found, quitting")
    #     print(frameinfo.filename, frameinfo.lineno)
    #     quit()
    soup = BeautifulSoup(data, 'html.parser')
    l=soup.find_all("content")
    prev=""
    for x in l:
        temp=x.get("src")
        temp1=temp.split("#")[0]
        if(prev==temp1):
            continue
        else:
            try:
                with open (global_root_dir+ temp1, "r") as xhtml_epub:
                    xhtml_data=xhtml_epub.read()
                    f.write(xhtml_data)
            except FileNotFoundError:
                print(global_root_dir + temp1 + ' not found, skipping...')
        prev=temp1
    f.close()
    f=open(global_root_dir+"temp.xhtml","r")
    writepdf(f.read())


def extract_zip_to_temp(path):
    with zipfile.ZipFile(path, 'r') as zip_ref:
        ret=zip_ref.extractall("/tmp/epub_temp/")

if __name__ == "__main__": 
    unzip_file_path=sys.argv[1]
    filename=unzip_file_path.split("/")[-1]
    print(filename)
    last4=filename[-4:]
    if(last4!="epub"):
        print("It's a {} file".format(last4))
        quit()
    shutil.copy(unzip_file_path,"/tmp/epub_temp.zip")
    try:
        shutil.rmtree("/tmp/epub_temp")
    except:
        print("")
    os.mkdir('/tmp/epub_temp')
    extract_zip_to_temp("/tmp/epub_temp.zip")
    global_root_dir="/tmp/epub_temp/"
    # print(unzip_file_path)
    filename=filename[:-5]
    generatepdf()
    shutil.rmtree("/tmp/epub_temp")
