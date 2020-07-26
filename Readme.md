# Instruction to Setup
1. conda env create -f environment.yml
2. source activate epub
3. python epub2pdf.py "{filepath}"
4. It will generate {filename}.pdf in current directory

# Known Bugs
1. Problem in image addition
2. Pdf Outline issues.
3. page change for each chapter.

# How it works
1. Epub is zipped file containing xhtml and metadata.
2. So I used weasyprint to convert xhtml to pdf.
3. But how to know which html to add first.
4. That information is contained in *.ncx inside epub bundle. BS4 is used to read ncx file.