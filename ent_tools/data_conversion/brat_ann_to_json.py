import argparse
import os

import logzero
from logzero import logger

from ent_tools.common.data_io import write_as_json
from ent_tools.data_conversion.brat_util import get_subdoc_spans, gen_doc_dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_txt', '-txt',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--input_ann', '-ann',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--output_json_dir', '-json_dir',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--output_json_name', '-json_name',
        type=str,
    )
    parser.add_argument(
        '--attributes',
        type=str,
    )
    parser.add_argument(
        '--split_by_subdoc',
        action='store_true',
    )
    args = parser.parse_args()

    if args.output_json_name:
        name = args.output_json_name
    else:
        name = os.path.basename(args.input_txt).split('.txt')[0]

    if args.split_by_subdoc:
        subdoc_spans = get_subdoc_spans(args.input_txt)
    else:
        subdoc_spans = None

    if args.attributes:
        attributes = args.attributes.split(',')
    else:
        attributes = None

    data = {}
    output_json_path = f'{args.output_json_dir}/{name}.json'
    if subdoc_spans:
        for i, subdoc_span in enumerate(subdoc_spans):
            doc_name = f'{name}-{i+1}'
            doc_dict = gen_doc_dict(args.input_txt,
                                    args.input_ann,
                                    att_keys=attributes,
                                    subdoc_span=subdoc_span)
            data[doc_name] = doc_dict
    else:
        doc_name = name
        doc_dict = gen_doc_dict(args.input_txt,
                                args.input_ann,
                                att_keys=attributes)
        data[doc_name] = doc_dict

    write_as_json(data, output_json_path)


if __name__ == '__main__':
    main()
