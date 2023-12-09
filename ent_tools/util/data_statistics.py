from collections import Counter

import spacy
from spacy import Language
from spacy.tokens import DocBin

from ent_tools.util.constants import DOC_ID, SENS, SEN_ID, MENS, ENT_TYPE
from ent_tools.nlp_tools.spacy.util import get_simple_span


def get_stats_from_dict(
        data: dict,
) -> Counter:

    c_basic = Counter()
    c_cate  = Counter()

    c_basic['n_document'] = len(data)

    for docid, doc in data.items():
        sens = doc[SENS]
        c_basic['n_sentence'] += len(sens)

        mens = doc[MENS]
        c_basic['n_mention'] += len(mens)

        for men_id, men in mens.items():
            etype = men[ENT_TYPE]
            c_cate[etype] += 1

    return c_basic, c_cate


def get_stats_from_docbin(
        data: DocBin,
        data_ids: list = None,
        nlp: Language = None,
) -> Counter:

    c_basic = Counter()
    c_cate  = Counter()

    if not nlp:
        nlp = spacy.blank('ja')

    if data_ids:
        c_basic['n_document'] = len(set([data_id[DOC_ID] for data_id in data_ids]))
        c_basic['n_sentence'] = len(set([f'{data_id[DOC_ID]}-{data_id[SEN_ID]}' 
                                         for data_id in data_ids]))
    else:
        c_basic['n_document'] = 0
        c_basic['n_sentence'] = 0

    # Note: spacy' Doc corresponds to usual sentence
    for doc in data.get_docs(nlp.vocab):
        ents_simple = [get_simple_span(span) for span in doc.ents]
        c_basic['n_mention'] += len(ents_simple)

        for (men_text, begin_tok, end_tok, etype) in ents_simple:
            c_cate[etype] += 1

    return c_basic, c_cate
