import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Tuple

from logzero import logger

sys.path.append('src')          # TODO remove
from common.constants import NON_ENTITY, SENS, TXT, MEN_IDS, MENS, SEN_ID, SPAN, ENT_TYPE


def load_id_list(
        path: str,
) -> list:

    id_list = []

    with open(path) as f:
        for line in f:
            line = line.strip('\n')

            if not (line.startswith('OC')
                    or line.startswith('OW')
                    or line.startswith('OY')
                    or line.startswith('PB')
                    or line.startswith('PM')
                    or line.startswith('PN')
            ):
                # convert id: e.g., A001n_OY04_00001 -> OY04_00001
                line = '_'.join(line.split('_')[1:])

            id_list.append(line)

    return id_list


def get_spans(
        texts: list,
        labels: list,
) -> list:

    begin = 0
    spans = []
    for text, label in zip(texts, labels):
        end = begin + len(text)

        if label != NON_ENTITY:
            spans.append((begin, end))
        else:
            spans.append(None)

        begin = end

    return spans


def parse_text_line(
        line: str,
) -> Tuple[list, list]:

    texts  = []
    labels = []

    try:
        root = ET.fromstring(f'<S>{line}</S>')
    except ET.ParseError as e:
        logger.warning(f'Merge multiple lines due to imcompleted tags: {line}')
        return False, None, None
    
    if len(root) == 0:
        texts = [root.text]
        labels = [NON_ENTITY]
        
    else:
        if root.text:
            texts.append(root.text)
            labels.append(NON_ENTITY)
        
        for child in root:
            if len(child) == 0:
                texts.append(child.text)
                labels.append(child.tag)

                if child.tail:
                    texts.append(child.tail)
                    labels.append(NON_ENTITY)

            elif len(child) == 1:
                schild = child[0]

                if len(schild) == 0:
                    # Example:
                    # <Rank>世界<Rank>一</Rank></Rank>の
                    # child:  text=世界, tag=Rank, tail=の
                    # schild: text=一,   tag=Rank, tail=None

                    child_text = (
                        (child.text if child.text else '')
                        + (schild.text if schild.text else '')
                        + (schild.tail if schild.tail else ''))
                    texts.append(child_text)
                    labels.append(child.tag)

                elif len(schild) == 1:
                    sschild = schild[0]

                    # Example:
                    # <Food_Other><Dish><Flora>昆布茶</Flora></Dish></Food_Other>が味の決め手。
                    # child:   text=None,   tag=Food_Other, tail=が味の決め手。
                    # schild:  text=None,   tag=Dish,       tail=None
                    # sschild: text=昆布茶, tag=Flora,      tail=None

                    child_text = (
                        (child.text if child.text else '')
                        + (schild.text if schild.text else '')
                        + (sschild.text if sschild.text else '')
                        + (sschild.tail if sschild.tail else '')
                        + (schild.tail if sschild.tail else ''))
                    texts.append(child_text)
                    # ignore nested tags
                    labels.append(child.tag)
                    
                else:
                    assert True, 'Unexpected nested tags'

                if child.tail:
                    texts.append(child.tail)
                    labels.append(NON_ENTITY)

            else:
                assert True, 'Unexpected nested tags'

    return True, texts, labels


def parse_xml(
        xml_path: str,
        id2doc: dict
) -> None:

    logger.info(f'Read: {xml_path}')
    with open(xml_path) as f:
        in_text = False

        doc_id = None
        sen_id = 0
        men_id = 0
        sentences = {}
        mentions  = {}
        line_stacked = ''

        for line in f:
            line = line.strip('\n')

            if not line:
                continue

            elif line.startswith('<ID>'):
                doc_id = line[line.index('>')+1:line.index('<', 1)]
            
            elif line.startswith('</TEXT>'):
                in_text = False

            elif line.startswith('<TEXT>'):
                in_text = True
                in_ne = False
                prev_ne_name = ''

            elif (line.startswith('<?xml') 
                  or line.startswith('<DOC>') 
                  or line.startswith('</DOC>') 
                  or line.startswith('<rejectedBlock')
            ):
                continue

            elif in_text:
                if line_stacked:
                    input_text = f'{line_stacked}{line}'
                else:
                    input_text = line

                success, texts, labels = parse_text_line(input_text)
                if success:
                    spans = get_spans(texts, labels)
                    sen_id += 1
                    sen_dict_key = f'S{sen_id}'
                    men_ids = []
     
                    for span, text, label in zip(spans, texts, labels):
                        if span:
                            men_id += 1
                            men_dict_key = f'M{men_id}'
                            men_ids.append(men_dict_key)
     
                            men_dict_val = {
                                SEN_ID: sen_dict_key, 
                                SPAN: span,
                                ENT_TYPE: label, 
                                TXT: text}
                            mentions[men_dict_key] = men_dict_val
     
                    sen_dict_val = {
                        TXT: ''.join(texts), 
                        MEN_IDS: men_ids}
                    sentences[sen_dict_key] = sen_dict_val

                    line_stacked = ''
                else:
                    line_stacked += line

            else:
                pass

        id2doc[doc_id] = {SENS: sentences, MENS: mentions}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', '--xml_top_dir', required=True)
    parser.add_argument('-j', '--json_output_path', required=True)
    parser.add_argument('-i',  '--id_list_path')
    parser.add_argument('--exclude_domains')
    args = parser.parse_args()

    id_list = None
    id2doc = {}

    if args.id_list_path:
        id_list = load_id_list(args.id_list_path)

    all_domains = ['OC', 'OW', 'OY', 'PB', 'PM', 'PN']
    if args.exclude_domains:
        domains = set(all_domains) - set(args.exclude_domains.split(','))
        domains = sorted(domains)

    else:
        domains = all_domains

    for domain in domains:
        dir_path = f'{args.xml_top_dir}/{domain}'
        for file_name in os.listdir(dir_path):
            file_id = file_name.split('.xml')[0]
            file_path = f'{dir_path}/{file_name}'

            if (not id_list
                or (id_list and file_id in id_list)
            ):
                if file_path.endswith('.xml'):
                    parse_xml(file_path, id2doc)

            else:
                logger.info(f'Skipped: {file_path}')                

    with open(args.json_output_path, 'w') as fw:
        json.dump(id2doc, fw, ensure_ascii=False, indent=2)
        logger.info(f'Saved: {args.json_output_path}')

    n_doc = len(id2doc)
    n_sen = 0
    n_men = 0

    for doc_id, doc in id2doc.items():
        n_sen += len(doc[SENS].keys())
        n_men += len(doc[MENS].keys())

    logger.info(f'No. of documents: {n_doc}')
    logger.info(f'No. of sentences: {n_sen}')
    logger.info(f'No. of NE mentions:  {n_men}')


if __name__ == '__main__':
    main()
