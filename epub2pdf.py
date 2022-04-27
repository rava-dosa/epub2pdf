import re
import shutil
import zipfile
import os
import time
import logging
import argparse
from sys import platform
from collections import defaultdict

import tinycss2
import css_inline
from tqdm import tqdm
from bs4 import BeautifulSoup
from weasyprint import HTML

from css_utils import *

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
    parser.add_argument("-s", "--sample", help="sample page to check", action="store_true")
    parser.add_argument("-f", "--font", help="config font", action="store_true")
    parser.add_argument("-r", "--ratio", help="config font by ratio", action="store_true")
    parser.add_argument("--sample_page", default=10, type=int, help="output pdf file of sample page")
    parser.add_argument("--font_size_ratio", default=1.2, help="font size ratio to original font size")
    parser.add_argument("--font_size", default=2.0,type=float, help="font size")
    parser.add_argument("--font_unit", default='em',type=str, help="font size unit 'em' or 'px'")
    parser.add_argument("--extract_dir", default=os.path.join(tmp_dir, "extract/"), help="temp dir")
    parser.add_argument("--extract_zip", default=os.path.join(tmp_dir, "epub_temp.zip"), help="temp zip file")
    parser.add_argument("--css_file", default=os.path.join(tmp_dir, "tmp.css"), help="temp css file")
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

class UpdateCSS():
    def __init__(self,root_dir,opf_name) -> None:
        self.url2file={}
        self.css_files=read_css(root_dir,opf_name)
    def update_css_files(self,files):
        self.css_files=files
    def add_css_files(self,files):
        self.css_files.extend(files)
    def pair_css_url(self,url):
        try:
            return self.url2file[url]
        except:
            for file in self.css_files:
                if os.path.basename(file) == os.path.basename(url):
                    self.url2file[url]=os.path.abspath(file)
                    return file
        logger.warning("css file not found: %s" % url)
        return ""

def process_css_url(data,css_updater):
    
    # replace relative css url to absolute url
    soup = BeautifulSoup(data, "lxml")
    css_items = soup.find_all("link", {"type": "text/css"})
    for item in css_items:
        css_url=item.get("href")
        css_file = css_updater.pair_css_url(css_url)
        data=data.replace(css_url,css_file)

    # not inline stylesheet css
    soup = BeautifulSoup(data, "lxml")
    css_items = soup.find_all("link", {"type": "text/css"})
    for item in css_items:
        if item.get("href") and os.path.basename(item.get("href"))=="stylesheet.css":
            item.decompose()
    data=css_inline.inline(soup.prettify())
    
    # remove other css
    soup = BeautifulSoup(data, "lxml")
    css_items = soup.find_all("style", {"type": "text/css"})
    for item in css_items:
        item.decompose()
    return soup.prettify()

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

def get_original_size(css_txt, content_cls):

    found_flag=False
    rules = tinycss2.parse_stylesheet(css_txt)
    for rule in rules:
        # print(rule)
        if type(rule) is not tinycss2.ast.WhitespaceToken:
            for token in rule.prelude:
                if token.value==content_cls:
                    found_flag=True
                    # print(tinycss2.parse_declaration_list(rule.content))
                    break
        if found_flag:
            break
    found_font_size_flag=False
    if found_flag:
        for token in rule.content:
            if not found_font_size_flag:
                if token.value=='font-size':
                    found_font_size_flag=True
                    continue
            if found_font_size_flag:
                if token.type=='dimension':
                    print(f'original font-size is  {token.value}{token.unit}')
                    return token.value,token.unit
    return None,None

def standard_unit(font_size,font_unit):
    if not font_size:
        return 2,'em'
    assert font_unit in ['em','px']
    # 1em=16px
    if font_unit == 'px':
        font_size = font_size/16
        font_unit='em'
    return font_size,font_unit


def config_css(args,root_dir,opf_name,content_cls_sorted):
    font_size,font_unit= args.font_size,args.font_unit
    font_size,font_unit=standard_unit(font_size,font_unit)

    content_cls=content_cls_sorted[0][0]
    print(f'set content class to {content_cls}')

    
    css_files = read_css(root_dir, opf_name)
    content_rule_list=[]
    for css_file in css_files:
        print("config css:", css_file)
        # process css file
        with open(css_file, "r", encoding="utf8") as f:
            css_txt=f.read()
        content_rule_list.append(custom_page_rule())
        if css_txt.find(content_cls) != -1:
            if args.ratio:
                start_idx=0
                ratio=args.font_size_ratio
            else:
                # 1. find content initial size
                origin_size,origint_unit=get_original_size(css_txt, content_cls)
                origin_size,origint_unit=standard_unit(origin_size,origint_unit)
                # 2. record ratio
                ratio=font_size/origin_size
                # 3. set content size to font_size 
                content_rule=custom_font_rule(content_cls,font_size=font_size,font_unit=font_unit)
                content_rule_list.append(content_rule)
                # 4. set others font size according to ratio
                start_idx=1
            for content_cls_sorted_item in content_cls_sorted[start_idx:]:
                print('process ', content_cls_sorted_item[0])
                origin_size,origint_unit=get_original_size(css_txt, content_cls_sorted_item[0])
                origin_size,origint_unit=standard_unit(origin_size,origint_unit)
                new_size=round(origin_size*ratio,2)
                content_rule=custom_font_rule(content_cls_sorted_item[0],font_size=new_size,font_unit=font_unit)
                content_rule_list.append(content_rule)
    with open(args.css_file, 'w', encoding="utf8") as f:
        for rule in content_rule_list:
            f.write(rule.serialize()+'\n')


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


def writepdf(args,temp_xhtml_path, filename, root_dir, opf_name):
    with open(temp_xhtml_path, "r", encoding="utf8") as f:
        file_data = f.read()
    css = read_css(root_dir, opf_name)
    if args.font:
        if os.path.exists(args.css_file):
            css.append(args.css_file)
        else:
            logging.warning(f"{args.css_file} not created")
    image_base = image_base_url(root_dir, opf_name)
    html = HTML(string=file_data, base_url=image_base, encoding="utf8")
    print("rendering html to pdf ...")
    start = time.time()
    html.write_pdf(filename, stylesheets=css)
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
    css_updater=UpdateCSS(root_dir,opf_name)
    with open(temp_xhtml_path, "w", encoding="utf8") as f:
        toc_files = get_files(root_dir, opf_name)
        prev = ""
        if sample:
            file_cnt = sample_page
        else:
            file_cnt = len(toc_files)

        content_cls_dict=defaultdict(int)
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
                    soup = BeautifulSoup(xhtml_data, "lxml")
                    for p in soup.find_all('p'):
                        try:
                            classes=p.get('class')
                            for cls in classes:
                                if cls not in ['center','right','left','justify']:
                                    content_cls_dict[cls]+=1
                        except:
                            pass
                    xhtml_data_m = process_href_tag(xhtml_data)
                    xhtml_data_m = process_css_url(xhtml_data_m,css_updater)
                    f.write(xhtml_data_m)
            prev = toc_file
        print(content_cls_dict)
        print(sorted(list(content_cls_dict.items()),key=lambda x:x[1], reverse=True))
        content_cls_sorted=sorted(list(content_cls_dict.items()),key=lambda x:x[1], reverse=True)

    return temp_xhtml_path,content_cls_sorted


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
    temp_xhtml_path,content_cls_sorted=generatepdf(extract_dir, opf_name, sample=args.sample, sample_page=args.sample_page)
    if args.font:
        config_css(args,extract_dir, opf_name,content_cls_sorted)
    writepdf(args,temp_xhtml_path, pdf_file_path, extract_dir, opf_name)
    if not args.debug:
        shutil.rmtree(extract_dir)

if __name__ == "__main__":
    main()

