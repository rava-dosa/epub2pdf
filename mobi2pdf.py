from bs4 import BeautifulSoup
from weasyprint import HTML, CSS, default_url_fetcher
import mobi
import shutil
import sys

if __name__ == "__main__": 
    unzip_file_path=sys.argv[1]
    tempdir, filepath = mobi.extract(unzip_file_path)
    image_base=filepath[:-9]
    html=HTML(filename=filepath,base_url=image_base,encoding="utf8")
    filename=unzip_file_path.split("/")[-1]
    html.write_pdf(filename+'.pdf')
    shutil.rmtree(tempdir)