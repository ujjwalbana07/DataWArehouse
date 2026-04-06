import pypdf

def extract_pdf(filename, outname):
    try:
        reader = pypdf.PdfReader(filename)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        with open(outname, 'w') as f:
            f.write(text)
        print(f"Extracted {filename} to {outname}")
    except Exception as e:
        print(f"Error extracting {filename}: {e}")

extract_pdf('Report_1_DW.pdf', 'report1.txt')
extract_pdf('Report2 - Group3.pdf', 'report2.txt')
extract_pdf('Report_3.pdf', 'report3.txt')
