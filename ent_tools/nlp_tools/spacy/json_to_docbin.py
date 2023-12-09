import argparse

from logzero import logger

from ent_tools.common.data_io import load_json
from ent_tools.common.data_statistics import get_stats_from_dict, get_stats_from_docbin
from ent_tools.nlp_tools.spacy.data_io import convert_dict_to_docbin


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model_name', '-m',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--input_json_path', '-i',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--output_path', '-o',
        type=str,
        required=True,
    )
    args = parser.parse_args()
    
    data_org = load_json(args.input_json_path)
    c_basic, c_cate = get_stats_from_dict(data_org)
    if 'n_document' in c_basic:
        logger.info(f'Num of documents: {c_basic["n_document"]}')
    if 'n_sentence' in c_basic:
        logger.info(f'Num of sentences: {c_basic["n_sentence"]}')
    if 'n_mention' in c_basic:
        logger.info(f'Num of mentions: {c_basic["n_mention"]}')

    data_docbin, data_ids = convert_dict_to_docbin(
        args.model_name, data_org, output_path=args.output_path)
    c_basic, c_cate = get_stats_from_docbin(data_docbin, data_ids)
    if 'n_document' in c_basic:
        logger.info(f'Num of documents: {c_basic["n_document"]}')
    if 'n_sentence' in c_basic:
        logger.info(f'Num of sentences: {c_basic["n_sentence"]}')
    if 'n_mention' in c_basic:
        logger.info(f'Num of mentions: {c_basic["n_mention"]}')


if __name__ == '__main__':
    main()
