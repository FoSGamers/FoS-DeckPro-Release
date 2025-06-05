import pdfplumber

PDF_PATH = 'live-7360a2db-6655-4313-ac3a-f99018783a84-all-slips-letter-size-5ed66f33.pdf'
OUTPUT_PATH = 'packing_slip_text.txt'

def main():
    with pdfplumber.open(PDF_PATH) as pdf:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as out:
            for i, page in enumerate(pdf.pages):
                out.write(f'--- PAGE {i+1} ---\n')
                text = page.extract_text()
                if text:
                    out.write(text + '\n')
                else:
                    out.write('[NO TEXT FOUND]\n')

if __name__ == '__main__':
    main() 