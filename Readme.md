# Instruction to Setup
1. conda env create -f environment.yml or pip install -r requirements.txt
2. source activate epub

# Epub2pdf
1. python epub2pdf.py "{filepath}"
2. It will generate {filename}.pdf in current directory

# Mobi2PDf
1. python mobi2pdf.pf "{filepath}"
2. It will generate {filename}.pdf in current directory

# Known Bugs
1. Pdf Outline issues.
2. page change for each chapter.
3. page lost

# Fix Bugs
- not support Chinese  
  use `encoding=utf8` when write/read files
- page lost  
 locate content files in content.opf instead of toc.ncx
- toc lost
  use regex to update hyperlink

# How it works [Epub]
1. Epub is zipped file containing xhtml and metadata.
2. So I used weasyprint to convert xhtml to pdf.
3. But how to know which html to add first.
4. That information is contained in *.ncx inside epub bundle. BS4 is used to read ncx file.

# How it works [Mobi]
1. Kindle unpack to extract data.
2. Weasyprint to convert html to pdf.

# Credits
1. [KindleUnpack](https://github.com/kevinhendricks/KindleUnpack)
2. [Weasyprint](https://github.com/Kozea/WeasyPrint)