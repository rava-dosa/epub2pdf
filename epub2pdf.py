import re
import shutil
import zipfile
import os
import time
import logging
import argparse
from sys import platform


from tqdm import tqdm
from bs4 import BeautifulSoup
from weasyprint import HTML
from weasyprint.fonts import FontConfiguration

if platform == "linux" or platform == "linux2":
    # linux
    tmp_dir = "/tmp"
else:
    tmp_dir = "tmp"
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--epub_file_path", help="input epub file")
    parser.add_argument("-o", "--pdf_file_path", help="output pdf file")
    parser.add_argument("-d", "--debug", help="debug mode", action="store_true")
    parser.add_argument("-s", "--sample", help="sample output", action="store_true")
    parser.add_argument("-c", "--sample_page", default=10, help="output pdf file")
    parser.add_argument("--extract_dir", default=os.path.join(tmp_dir, "extract/"), help="temp dir")
    parser.add_argument("--extract_zip", default=os.path.join(tmp_dir, "epub_temp.zip"), help="temp zip file")
    args = parser.parse_args()
    return args

logger = logging.getLogger("weasyprint")
logger.addHandler(logging.FileHandler(os.path.join(tmp_dir, "weasyprint.log")))


def image_base_url(root_dir, opf_name):
    f = open(os.path.join(root_dir, opf_name), "r", encoding="utf8")
    soup = BeautifulSoup(f.read(), "lxml")
    a = soup.find("manifest")
    try:
        img_jpgs = soup.find_all("item", {"media-type": "image/jpeg"})
        for img_jpg in img_jpgs:
            try:
                if len(img_jpg.get("href").split("/")) > 1:
                    img_url = img_jpg.get("href").split("/")[0]
                    image_base = root_dir + img_url + "/"
                    return
            except Exception as e:
                print(e)

                pass
    except:
        print("no jpeg")
    try:
        img_png = a.find("item", {"media-type": "image/png"}).get("href")
        image_base = root_dir + img_png.split("/")[0] + "/"
    except:
        print("no png")
    return image_base


def get_files(root_dir, opf_name):
    ret = []
    f = open(os.path.join(root_dir, opf_name), "r", encoding="utf8")
    soup = BeautifulSoup(f.read(), "lxml")
    xml_files = soup.find_all("item", {"media-type": "application/xhtml+xml"})
    if xml_files is None:
        print("xml not found")
    else:
        for xml_file in xml_files:
            ret.append(xml_file.get("href"))
    return ret


def read_css(root_dir, opf_name):
    ret = []
    f = open(os.path.join(root_dir, opf_name), "r", encoding="utf8")
    soup = BeautifulSoup(f.read(), "lxml")
    css_files = soup.find_all("item", {"media-type": "text/css"})
    if css_files is None:
        print("Css not found")
    else:
        for css_file in css_files:
            ret.append(os.path.join(root_dir,  css_file.get("href")))
    return ret


def get_opf_name(root_dir):
    f = open(os.path.join(root_dir, "META-INF/", "container.xml"), "r", encoding="utf8")
    data = f.read()
    soup = BeautifulSoup(data, "html.parser")
    l = soup.find_all("rootfile")
    if len(l) == 0:
        raise Exception(f"no rootfile found")

    else:
        l1 = l[0]
        pathx = l1.get("full-path")
        if "/" in pathx:
            splitx = pathx.split("/")
            root_dir = root_dir + splitx[0] + "/"
            opf_name = splitx[1]
        else:
            opf_name = pathx
    return opf_name


def writepdf(temp_xhtml_path, filename, root_dir, opf_name):
    with open(temp_xhtml_path, "r", encoding="utf8") as f:
        file_data = f.read()
    font_config = FontConfiguration()
    css = read_css(root_dir, opf_name)
    image_base = image_base_url(root_dir, opf_name)
    html = HTML(string=file_data, base_url=image_base, encoding="utf8")
    print("rendering html to pdf ...")
    start = time.time()
    html.write_pdf(filename, stylesheets=css, font_config=font_config)
    print("rendering time {0:f} s,".format((time.time() - start)))
    print("finished! save to ", filename)
    



def get_href(matched, startStr="href=", endStr="#"):
    patternStr = matched.group()
    if patternStr.find("'") != -1:
        middleStr = "'"
    elif patternStr.find('"') != -1:
        middleStr = '"'
    else:
        raise Exception("no quotation mark")
    return startStr + middleStr + endStr


def process_href_tag(data):
    startStr = "href="
    endStr = "#"
    patternStr = r'%s(["\' ]+)(.*?)%s' % (startStr, endStr)
    p = re.compile(patternStr, re.IGNORECASE)
    file_data_m = re.sub(p, get_href, data, count=0, flags=0)
    return file_data_m


def generatepdf(root_dir, opf_name, sample=False, sample_page=10):
    temp_xhtml_path=os.path.join(root_dir, "temp.xhtml")
    with open(temp_xhtml_path, "w", encoding="utf8") as f:
        toc_files = get_files(root_dir, opf_name)
        prev = ""
        if sample:
            file_cnt = sample_page
        else:
            file_cnt = len(toc_files)
        progress_bar = tqdm(range(file_cnt), desc="Generating PDF")

        for i, toc_file in zip(progress_bar, toc_files):
            progress_bar.set_description(f"{i+1}/{file_cnt}")
            if prev == toc_file:
                continue
            else:
                with open(
                    os.path.join(root_dir, toc_file), "r", encoding="utf8"
                ) as xhtml_epub:
                    xhtml_data = xhtml_epub.read()
                    xhtml_data_m = process_href_tag(xhtml_data)
                    f.write(xhtml_data_m)
            prev = toc_file

    return temp_xhtml_path


def extract_zip_to_temp(args):
    epub_file_path=args.epub_file_path
    extract_zip=args.extract_zip
    extract_dir=args.extract_dir
    shutil.copy(epub_file_path, extract_zip)
    try:
        shutil.rmtree(extract_dir)
    except:
        print("")
    os.mkdir(extract_dir)
    with zipfile.ZipFile(extract_zip, "r") as zip_ref:
        ret = zip_ref.extractall(extract_dir)
    print('extract epub to ',extract_dir)

def process_filename(args):
    filename = os.path.basename(args.epub_file_path)
    file_prefix = filename.split(".")[0]
    file_suffix = filename.split(".")[-1]
    if file_suffix != "epub":
        raise Exception(f"not a epub file, It's a {file_suffix} file")
        
    if not args.pdf_file_path:
        pdf_file_path = file_prefix + ".pdf"
    else:
        pdf_file_path=args.pdf_file_path
    return pdf_file_path

def main():
    args = parse_args()
    extract_dir=args.extract_dir
    pdf_file_path=process_filename(args)

    extract_zip_to_temp(args)
    
    opf_name = get_opf_name(extract_dir)
    temp_xhtml_path=generatepdf(extract_dir, opf_name, sample=args.sample, sample_page=args.sample_page)
    writepdf(temp_xhtml_path, pdf_file_path, extract_dir, opf_name)
    if not args.debug:
        shutil.rmtree(extract_dir)

if __name__ == "__main__":
    main()

