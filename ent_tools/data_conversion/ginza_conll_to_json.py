import argparse
import os
import sys

from logzero import logger

from ent_tools.util.constants import NON_ENTITY, SENS, SEN_ID, TXT, MEN_IDS, MENS, SPAN, ENT_TYPE
from ent_tools.util.data_io import load_json, write_as_json
from ent_tools.data_conversion.util import read_tsv, get_spans_from_BIO_seq


def gen_doc_dict(
        conll_path: str,
        tsv_path: str = None,
        labelmap: dict = None,
) -> None:

    sen = None
    words = []
    labels = []

    doc_dict  = {SENS: {}, MENS: {}}
    men_id_num = 0
    sen_id_num = 0

    tsv_reader = read_tsv(tsv_path) if tsv_path else None

    with open(conll_path) as f:
        logger.info(f'Read: {conll_path}')
        for line in f:
            line = line.rstrip('\n')

            if line.startswith('#'):
                continue

            elif not line:
                sen_id_num += 1
                sen_id = f'{sen_id_num:03d}'
                sen = ''.join(words)
                sen_dict = {TXT: sen, MEN_IDS: []}
                doc_dict[SENS][sen_id] = sen_dict

                if tsv_reader:
                    _, sen_tsv = tsv_reader.__next__()
                    assert sen == sen_tsv

                spans = get_spans_from_BIO_seq(words, labels)
                for span in spans:
                    begin = span[0]
                    end   = span[1]
                    label = span[2]
                    if labelmap:
                        if label in labelmap:
                            label = labelmap[label]
                        else:
                            continue

                    if sen[end-1] == '　':
                        end -= 1

                    span_text = sen[begin:end]

                    men_id_num += 1
                    men_id = f'{men_id_num:03d}'
                    sen_id = f'{sen_id_num:03d}'
                    men_dict = {SEN_ID: sen_id,
                                SPAN: (begin, end),
                                ENT_TYPE: label,
                                TXT: span_text,}
                    doc_dict[MENS][men_id] = men_dict
                    sen_dict[MEN_IDS].append(men_id)

                sen = None
                words = []
                labels = []
                
            else:
                array = line.split('\t')
                word  = array[1]
                attrs = array[9].split('|')
                ene   = NON_ENTITY
                space_after = False
                for attr in attrs:
                    if attr == 'SpaceAfter=Yes':
                        space_after = True
                    elif attr.startswith('ENE'):
                        ene = attr[4:]

                words.append(word)
                labels.append(ene)

                if space_after:
                    words.append(' ')
                    labels.append(NON_ENTITY)

    return doc_dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_conll', '-conll', required=True)
    parser.add_argument('--output_json', '-json', required=True)
    parser.add_argument('--tsv_with_text_span', '-tsv', dest='tsv')
    parser.add_argument('--label_conversion_map_path', '-label')
    args = parser.parse_args()
    
    labelmap = None
    if args.label_conversion_map_path:
        labelmap = load_json(args.label_conversion_map_path)

    doc_name = os.path.basename(args.input_conll).split('.conll')[0]
    doc_dict = gen_doc_dict(args.input_conll, tsv_path=args.tsv, labelmap=labelmap)
    data = {doc_name: doc_dict}
    write_as_json(data, args.output_json)


if __name__ == '__main__':
    main()
