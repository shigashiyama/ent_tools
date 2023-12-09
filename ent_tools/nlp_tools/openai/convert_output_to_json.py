import argparse
import os
import sys
from typing import Tuple

from logzero import logger

sys.path.append('src')          # TODO remove
from common.constants import DOC_ID, SENS, SEN_ID, TXT, MEN_IDS, MENS, SPAN, ENT_TYPE
from common.data_io import write_as_json


def get_spans(
        text: str,
        res_str: str,
) -> list[Tuple]:

    spans = []

    if res_str in (None, 'None', '[]'):
        return spans

    cur_index = 0
    for mention_str in res_str.strip('[]').split(';'):
        if '","' in mention_str:
            mention_text_, label_ = mention_str.split('","')
        else:
            mention_text_, label_ = mention_str.split(',')
        men_text = mention_text_.strip(' "')
        label = label_.strip(' "')

        if not men_text in text[cur_index:]:
            logger.warning(f'Recognized mention "{men_text}" is skipped because it is not in input text with offset>={cur_index} "{text[cur_index:]}\nfull_text="{text}"\nfull_result="{res_str}"')
            continue

        begin = text.index(men_text, cur_index)
        end = begin + len(men_text)
        spans.append((men_text, (begin, end), label))
        cur_index = end

    return spans


def read_result(
        input_result_path: str,
) -> dict:

    doc_dict  = {SENS: {}, MENS: {}}
    sen_id = 1
    men_id = 1

    with open(input_result_path) as f:
        for line in f:
            line = line.strip('\n')

            array = line.split('\t')
            assert len(array) >= 2
            text = array[0]
            res_str = array[1]
            if not text:
                continue

            sen_key = f'{sen_id:03d}'
            spans = get_spans(text, res_str)
            men_ids = []

            for span in spans:
                men_key = f'{men_id:03d}'
                men_text = span[0]
                span_indexes = span[1]
                etype = span[2]
                men_dict = {SEN_ID: sen_key,
                            SPAN: (span_indexes[0], span_indexes[1]),
                            ENT_TYPE: etype,
                            TXT: men_text,}

                doc_dict[MENS][men_key] = men_dict
                men_ids.append(men_key)
                men_id += 1

            sen_dict = {TXT: text, MEN_IDS: men_ids}
            doc_dict[SENS][sen_id] = sen_dict
            sen_id += 1

    return doc_dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_result_path', '-i',
        required=True,
    )
    parser.add_argument(
        '--output_json_path', '-o',
        required=True,
    )
    args = parser.parse_args()

    doc_id = os.path.basename(args.input_result_path).split('.')[0]
    doc_dict = read_result(args.input_result_path)
    data = {doc_id: doc_dict}
    write_as_json(data, args.output_json_path)


if __name__ == "__main__":
    main()
