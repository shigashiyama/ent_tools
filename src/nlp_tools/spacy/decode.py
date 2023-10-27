import argparse
import json
import os
import sys

from logzero import logger

from spacy import Language
from spacy.tokens import DocBin, Doc

sys.path.append('src')          # TODO remove
from common.constants import DOC_ID, SENS, SEN_ID, TXT, MEN_IDS, MENS, SPAN, ENT_TYPE
from nlp_tools.spacy.data_io import load_spacy_data
from nlp_tools.spacy.util import get_simple_span, load_model, prepare_ner_model


def decode_and_save_as_json(
        nlp: Language,
        doc_bin: DocBin,
        data_ids: list,
        output_path: str,
        save_per_doc: bool = True,
) -> None:

    if save_per_doc:
        output_dir = output_path
        assert os.path.isdir(output_dir)
    else:
        data_dict = {}

    prev_doc_id = None
    docs = list(doc_bin.get_docs(nlp.vocab))
    texts = [str(doc) for doc in docs]
    for i, (doc, doc_parsed) in enumerate(zip(docs, nlp.pipe(texts))):
        if (i+1) % 100 == 0:
            logger.info(f'Parsed {i+1} sentences.')

        ids = data_ids[i]
        doc_id = ids[DOC_ID]
        sen_id = ids[SEN_ID]

        if doc_id != prev_doc_id:
            if prev_doc_id:
                if save_per_doc:
                    output_path_ = f'{output_dir}/{prev_doc_id}.json'
                    with open(output_path_, 'w') as fw_:
                        json.dump({prev_doc_id: doc_dict}, fw_, ensure_ascii=False, indent=2)
                    logger.info(f'Saved: {output_path_}')
                else:
                    data_dict[prev_doc_id] = doc_dict

            doc_dict  = {SENS: {}, MENS: {}}
            men_id    = 0

        prev_doc_id = doc_id

        text = str(doc)
        doc_parsed = nlp(text)
        ents_simple = [get_simple_span(span) for span in doc_parsed.ents]

        sum_len = 0
        char_begin_idxs = [-1] * len(doc_parsed)
        char_end_idxs   = [-1] * len(doc_parsed)
        for i, tok in enumerate(doc_parsed):
            char_begin_idxs[i] = sum_len
            sum_len += len(tok)
            char_end_idxs[i] = sum_len

        men_ids = []
        for men_text, men_begin_tok, men_end_tok, men_etype in ents_simple:
            # token index -> char index
            men_begin = char_begin_idxs[men_begin_tok]
            men_end   = char_end_idxs[men_end_tok-1]
            men_id  += 1
            men_key  = f'T{men_id}'
            men_dict = {SEN_ID: sen_id,
                        SPAN: (men_begin, men_end),
                        ENT_TYPE: men_etype,
                        TXT: men_text,}

            doc_dict[MENS][men_key] = men_dict
            men_ids.append(men_key)

        sen_dict = {TXT: text, MEN_IDS: men_ids}
        doc_dict[SENS][sen_id] = sen_dict

    if doc_dict:
        if save_per_doc:
            output_path_ = f'{output_dir}/{prev_doc_id}.json'
            with open(output_path_, 'w') as fw_:
                json.dump({prev_doc_id: doc_dict}, fw_, ensure_ascii=False, indent=2)
            logger.info(f'Saved: {output_path_}')
        else:
            data_dict[prev_doc_id] = doc_dict

    if not save_per_doc:
        with open(output_path, 'w') as fw:
            json.dump(data_dict, fw, ensure_ascii=False, indent=2)
        logger.info(f'Saved: {output_path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--model_name', '-m',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--input_docbin_path', '-i',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--output_json_path', '-o',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--save_per_doc',
        action='store_true'
    )
    args = parser.parse_args()

    # load model
    nlp = load_model(args.model_name)
    prepare_ner_model(nlp)

    # load data    
    data, data_ids = load_spacy_data(args.input_docbin_path)

    # decode
    decode_and_save_as_json(nlp, data, data_ids, args.output_json_path, args.save_per_doc)


if __name__ == '__main__':
    main()
