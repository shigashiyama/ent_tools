from typing import Tuple

from logzero import logger

import spacy
from spacy import Language
from spacy.tokens import DocBin, Doc, Span



def get_simple_span(
        span: Span,
) -> Tuple:

    doc = span.doc
    span_text = ''.join([str(tok) for tok in doc[span.start:span.end]])
    label_str = doc.vocab.strings[span.label]
    simple_span = (span_text, span.start, span.end, label_str)
    return simple_span


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
