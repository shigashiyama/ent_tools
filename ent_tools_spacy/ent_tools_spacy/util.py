from collections import Counter
from typing import Tuple

from logzero import logger

import spacy
from spacy import Language
from spacy.tokens import DocBin, Doc, Span

from ent_tools.util.constants import DOC_ID, SEN_ID


def get_simple_span(
        span: Span,
) -> Tuple:

    doc = span.doc
    span_text = ''.join([str(tok) for tok in doc[span.start:span.end]])
    label_str = doc.vocab.strings[span.label]
    simple_span = (span_text, span.start, span.end, label_str)
    return simple_span


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


def load_model(
        model_name: str,        
) -> Language:
    
    if model_name.startswith('blank_'):
        lang = model_name.split('_')[1]
        nlp = spacy.blank(lang)
        logger.info(f'Use blank_ja pipeline instead of loading a model.')
    else:
        nlp = spacy.load(model_name)
        logger.info(f'Loaded model: {model_name}')

    return nlp


def prepare_ner_model(
        nlp: Language,
) -> None:

    logger.info(f'abled_pipes: {nlp.pipe_names}')
    use_pipes = ['transformer', 'ner']
    for pipe in nlp.pipe_names:
        if not pipe in use_pipes:
            nlp.disable_pipes(pipe)
    logger.info(f'abled_pipes: {nlp.pipe_names}')
