import argparse

from logzero import logger

from ent_tools.util.constants import SENS, MENS, TXT, MEN_IDS, SPAN, ENT_TYPE
from ent_tools.util.data_io import load_json


def read_and_write(
        input_json: str,
        output_tsv: str
) -> None:

    data = load_json(input_json)

    with open(output_tsv, 'w') as fw:
        for doc_id, doc in data.items():
            for sen_id, sen in doc[SENS].items():
                sen_text = sen[TXT]
        
                mens_str_list = []
                for men_id in sen[MEN_IDS]:
                    men = doc[MENS][men_id]
                    men_span = men[SPAN]
                    men_text = men[TXT]
                    etype = men[ENT_TYPE]
                    mens_str_list.append(f'{men_span[0]},{men_span[1]},{men_text},{etype}')
        
                mens_str = ';'.join(mens_str_list)
                fw.write(f'{sen_text}\t{mens_str}\n')

    logger.info(f'Save: {output_tsv}')
                    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input_json', required=True)
    parser.add_argument('-o', '--output_tsv', required=True)
    args = parser.parse_args()

    read_and_write(args.input_json, args.output_tsv)


if __name__ == '__main__':
    main()
