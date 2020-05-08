import sys
import fitz
import csv
import json
from tqdm import tqdm


def main(argvs):
    """メイン処理"""
    argvs = sys.argv
    argc = len(argvs)
    if argc != 3:
        print("Usage #python %s [JSONパス] [出力パス]" % argvs[0])
        exit()
    json_path = argvs[1]
    out_path = argvs[2]
    with open(json_path, mode='r', encoding='utf8') as fp:
        json_info = json.load(fp)

    string_path = json_info['string_path']
    string_info = {}
    with open(string_path, 'r', encoding='utf8', newline="\n") as fp:
        reader = csv.reader(fp)
        for row in reader:
            string_info[row[0].strip()] = row[1]
    doc = fitz.open(json_info['input_path'])

    for text_block in tqdm(json_info["text_block"]):
        txt = text_block['text'].strip()
        if txt in string_info:
            txt = string_info[txt]
            page = doc[text_block['page']]
            page.addTextAnnot(
                (text_block['x1'] - 20, text_block['y1'] - 20),
                txt
            )
        else:
            print("翻訳に失敗：", text_block['text'])

    doc.save(out_path, garbage=1, clean=1, deflate=1) 

if __name__ == '__main__':
    main(sys.argv)
