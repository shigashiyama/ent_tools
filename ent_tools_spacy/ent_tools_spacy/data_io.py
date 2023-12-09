import json
import os
from typing import Tuple

from logzero import logger

import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans

from ent_tools.util.constants import DOC_ID, SENS, SEN_ID, TXT, MEN_IDS, MENS, SPAN, ENT_TYPE
from ent_tools_spacy.util import load_model


def load_spacy_data(
        data_path: str,
) -> Tuple[DocBin, list]:

    data = DocBin()
    data.from_disk(data_path)
    logger.info(f'Loaded data: {data_path}')

    data_ids_path = f'{data_path}.ids'
    data_ids = []
    if os.path.isfile(data_ids_path):
        with open(data_ids_path) as f:
            for line in f:
                line = line.strip('\n')
                line_dict = json.loads(line)
                data_ids.append(line_dict)

    return data, data_ids


def convert_dict_to_docbin(
        model_name: str,
        data_org: dict,
        output_path: str = None,
) -> Tuple[DocBin, list]:

    if output_path:
        output_path_sen_ids = f'{output_path}.ids'
        fw = open(output_path_sen_ids, 'w')    

    nlp = load_model(model_name)
    docbin = DocBin()
    data_ids = []
    for docid, d_doc in data_org.items():
        d_mens = d_doc[MENS]

        for sen_id, d_sen in d_doc[SENS].items():
            user_data = {DOC_ID: docid, SEN_ID: sen_id}
            data_ids.append(user_data)
            if fw:
                fw.write(json.dumps(user_data, ensure_ascii=False)+'\n')

            text = d_sen[TXT]
            doc  = nlp.make_doc(text)

            ents = []
            men_ids = d_sen[MEN_IDS]
            for men_id in men_ids:
                d_men = d_mens[men_id]
                begin = d_men[SPAN][0]
                end   = d_men[SPAN][1]
                etype = d_men[ENT_TYPE]
                span = doc.char_span(begin, end, label=etype)

                if span:
                    ents.append(span)
                else:
                    logger.warning(f"Skipped mention='{text[begin:end]}' due to tokenization mismatch in sentence='{text}'")

            filtered_ents = filter_spans(ents)
            doc.ents = filtered_ents
            docbin.add(doc)

        logger.info(f'Added doc_id={docid}')
    
    if output_path:
        docbin.to_disk(output_path)
        logger.info(f'Saved: {output_path}')

        fw.close()
        logger.info(f'Saved: {output_path_sen_ids}')

    return docbin, data_ids
