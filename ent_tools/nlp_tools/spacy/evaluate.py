import argparse

import logzero
from logzero import logger

import spacy
from spacy import Language
from spacy.scorer import Scorer
from spacy.training import Example
from spacy.tokens import DocBin

from ent_tools.common.data_io import load_json
from ent_tools.nlp_tools.spacy.data_io import load_spacy_data
from ent_tools.nlp_tools.spacy.util import load_model, prepare_ner_model


def get_score_string(
        scores: dict,
) -> str:

    ret = f'Cate\tPrec\tRecall\tF1\n'

    p, r, f = (scores['ents_p'], scores['ents_r'], scores['ents_f'])
    ret += f'ALL\t{p:.3f}\t{r:.3f}\t{f:.3f}\n'

    for etype, et_scores in scores['ents_per_type'].items():
        p, r, f = (et_scores['p'], et_scores['r'], et_scores['f'])
        ret += f'{etype}\t{p:.3f}\t{r:.3f}\t{f:.3f}\n'

    return ret.rstrip('\n')

    
def evaluate(
        nlp: Language,
        doc_bin: DocBin,
        labelmap: dict = None,
) -> None:

    examples = []
    docs = list(doc_bin.get_docs(nlp.vocab))
    texts = [str(doc) for doc in docs]
    for i, (doc, doc_parsed) in enumerate(zip(docs, nlp.pipe(texts))):
        if (i+1) % 100 == 0:
            logger.info(f'Parserd {i+1} sentences.')

        for tok in doc_parsed:
            logger.debug(f'- tok={tok}, tok.ent_type={tok.ent_type} ({doc.vocab.strings[tok.ent_type]})')
            if labelmap:
                ent_type_str = doc.vocab.strings[tok.ent_type]
                if ent_type_str in labelmap:
                    new_ent_type_str = labelmap[ent_type_str]
                    tok.ent_type = doc.vocab.strings[new_ent_type_str]

        example = Example(doc_parsed, doc)
        examples.append(example)

    scorer = Scorer()
    results = scorer.score(examples)

    return results


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
        '--label_conversion_map_path', '-l',
        type=str,
        default=None,
    )
    args = parser.parse_args()

    logzero.loglevel(20)

    # load model
    nlp = load_model(args.model_name)
    prepare_ner_model(nlp)

    # label map
    labelmap = None
    if args.label_conversion_map_path:
        labelmap = load_json(args.label_conversion_map_path)

    # load docbin data
    data, _ = load_spacy_data(args.input_docbin_path)

    # evaluate
    scores = evaluate(nlp, data, labelmap=labelmap)
    logger.info('Note: The displayed scores may not be accurate because loaded gold data as spaCy\'s DocBin could exlclude some entity mentions whose char spans were not able to be converted to tokinizer-based token spans.')
    print(get_score_string(scores))


if __name__ == '__main__':
    main()
