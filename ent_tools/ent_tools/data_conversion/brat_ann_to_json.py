import argparse
import os

import logzero
from logzero import logger

from ent_tools.data_conversion.atd_util import convert_json_for_atd
from ent_tools.data_conversion.jel_util import convert_json_for_jel
from ent_tools.data_conversion.brat_util import get_subdoc_spans, gen_doc_dict
from ent_tools.data_conversion.json_util import check_attributes, segment_sentence_in_doc_dict
from ent_tools.util.data_io import load_jsonl, write_as_json

import json                     # tmp


ATD = 'atd'
JEL = 'jel'


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
        '--coref_tag_name',
        type=str,
    )
    parser.add_argument(
        '--directed_coref_tag_name',
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
    parser.add_argument(
        '--resegment_sentence',
        action='store_true',
    )
    parser.add_argument(
        '--unset_section_id',
        action='store_true',
    )
    parser.add_argument(
        '--data_style',
        type=str,
        choices=(ATD, JEL),
    )
    parser.add_argument(
        '--kb_info_jsonl_path',
        type=str,
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

    if args.kb_info_jsonl_path:
        kb_data = load_jsonl(args.kb_info_jsonl_path)
    else:
        kb_data = None

    data = {}
    output_json_path = f'{args.output_json_dir}/{name}.json'
    if subdoc_spans:
        meta_text = None
        with open(args.input_txt) as f:
            for line in f:
                if line.startswith('<doc'):
                    meta_text = line.rstrip()
                    break

        for i, subdoc_span in enumerate(subdoc_spans):
            doc_name = f'{name}-{i+1}'
            doc_dict = gen_doc_dict(
                args.input_txt, args.input_ann,
                att_keys=attributes,
                subdoc_span=subdoc_span,
                coref_tag_name=args.coref_tag_name,
                directed_coref_tag_name=args.directed_coref_tag_name,
                assign_section_id=not args.unset_section_id,
            )

            if args.data_style:
                if args.data_style == ATD:
                    doc_dict = convert_json_for_atd(doc_dict)

                elif args.data_style == JEL:
                    doc_dict = convert_json_for_jel(doc_dict, docid=name, kb_data=kb_data)

            if args.resegment_sentence:
                doc_dict = segment_sentence_in_doc_dict(doc_dict)

            if meta_text:
                doc_dict['meta_info'] = {'text': meta_text}
            check_attributes(doc_dict)
            data[doc_name] = doc_dict

    else:
        doc_name = name
        doc_dict = gen_doc_dict(
            args.input_txt, args.input_ann,
            att_keys=attributes,
            coref_tag_name=args.coref_tag_name,
            directed_coref_tag_name=args.directed_coref_tag_name,
            assign_section_id=not args.unset_section_id,
        )

        if args.data_style:
            if args.data_style == ATD:
                doc_dict = convert_json_for_atd(doc_dict)

            elif args.data_style == JEL:
                doc_dict = convert_json_for_jel(doc_dict, docid=name, kb_data=kb_data)

        if args.resegment_sentence:
            doc_dict = segment_sentence_in_doc_dict(doc_dict)

        check_attributes(doc_dict)
        data[doc_name] = doc_dict

    write_as_json(data, output_json_path)


if __name__ == '__main__':
    main()
