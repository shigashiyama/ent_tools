import argparse

from logzero import logger

from ent_tools.util.constants import DOC_ID, SENS, MENS, TXT, MEN_IDS, SPAN, ENT_TYPE
from ent_tools.util.data_io import load_json


XML_DEC_LINE = '<?xml version="1.0" encoding="utf-8" ?>'
DOC_BEGIN    = "<document>"
DOC_END      = "</document>"
TXT_BEGIN    = "<text>"
TXT_END      = "</text>"
MEN_BEGIN    = "<mention>"
MEN_END      = "</mention>"


def read_and_write(
        input_json: str,
        output_xml: str
) -> None:

    data = load_json(input_json)

    with open(output_xml, 'w') as fw:
        for doc_id, doc in data.items():
            fw.write(f'{XML_DEC_LINE}\n')
            if doc_id:
                fw.write(f'{DOC_BEGIN[:-1]} {DOC_ID}="{doc_id}">\n')
            else:
                fw.write(f'{DOC_BEGIN}\n')
            fw.write(f'{TXT_BEGIN}\n')

            for sen_id, sen in doc[SENS].items():
                sen_text = sen[TXT]
             
                sen_new = ''
                sen_new_wo_tag = ''
                prev_span_end = 0

                mens_str_list = []
                for men_id in sen[MEN_IDS]:
                    men = doc[MENS][men_id]
                    men_span = men[SPAN]
                    men_text = men[TXT]
                    etype = men[ENT_TYPE]
                    sen_new += f'{sen_text[:men[SPAN][0]]}<mention entity_type="{etype}">{men_text}{MEN_END}'
                    sen_new_wo_tag += f'{sen_text[prev_span_end:men[SPAN][0]]}{men_text}'
                    prev_span_end = men_span[1]

                if prev_span_end < len(sen_text):
                    sen_new += sen_text[prev_span_end:]
                    sen_new_wo_tag += sen_text[prev_span_end:]

                assert sen_new_wo_tag == sen_text
                fw.write(f'{sen_new}\n')

                # fw.write(f'{sen_text}\t{mens_str}\n')
                # print(f'{sen_text}\t{mens_str}')
            fw.write(f'{TXT_END}\n')
            fw.write(f'{DOC_END}\n')

    logger.info(f'Save: {output_xml}')
                    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_json', required=True)
    parser.add_argument('-o', '--output_xml', required=True)
    args = parser.parse_args()

    read_and_write(args.input_json, args.output_xml)


if __name__ == '__main__':
    main()
