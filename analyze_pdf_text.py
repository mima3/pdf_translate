import sys
import fitz
import csv
import json
from tqdm import tqdm


def main(input_path):
    argvs = sys.argv
    argc = len(argvs)
    if argc != 2:
        print("Usage #python %s [PDFパス]" % argvs[0])
        exit()
    input_path = argvs[1]
    doc = fitz.open(input_path)
    list_string = []
    result = []
    pno = 0
    for page in tqdm(doc):
        blocklist = page.getText('blocks')
        for block in blocklist:
            r = fitz.Rect(block[0], block[1], block[2], block[3])
            txt = block[4].replace('\n', '').replace('\r', '')
            result.append({
                'page' : pno,
                'x0' : block[0],
                'y0' : block[1],
                'x1' : block[2],
                'y1' : block[3],
                'text' : txt,
                'block_type' : block[5],
                'block_no' : block[6],
            })
            if not txt in list_string:
                list_string.append(txt)
        pno += 1

    string_path = '{}.csv'.format(input_path)
    with open(string_path, 'w', encoding='utf8', newline="") as fp:
        writer = csv.writer(fp)
        for s in list_string:
            writer.writerow([s, 'todo'])
    data = {
        "input_path" : input_path,
        "string_path" : string_path,
        "text_block" : result
    }
    with open('{}.json'.format(input_path), mode='w', encoding='utf8') as fp:
        json.dump(data, fp, sort_keys=True, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main(sys.argv)
