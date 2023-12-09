from logzero import logger

from common.constants import NON_ENTITY


def read_tsv(
        tsv_path: str,
) -> None:

    with open(tsv_path) as f:
        logger.info(f'Read: {tsv_path}')
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue

            array = line.split('\t')
            if not array[3]:
                continue

            begin_global = int(array[1])
            end_global   = int(array[2])
            sen          = array[3]
            yield (begin_global, sen)

    StopIteration


def get_spans_from_BIO_seq(
        words: list,
        labels: list,
) -> list:

    spans = []
    span_begin = -1
    char_idx = 0
    prev_tag  = None
    prev_cate = None
    for word, label in zip(words, labels):
        if label != NON_ENTITY:
            tag, cate = label.split('-')

            if prev_cate == None: # None VS B/I-X
                span_begin = char_idx
                prev_tag   = tag
                prev_cate  = cate

            elif prev_cate != cate or tag == 'B': # B/I-X VS B/I-Y or B-X
                spans.append((span_begin, char_idx, prev_cate))
                span_begin = char_idx
                prev_tag   = tag
                prev_cate  = cate

            elif tag == 'I':    # B/I-X VS B-X
                pass

        else:
            if prev_cate != None: # B/I-X VS None
                spans.append((span_begin, char_idx, prev_cate))
                span_begin = -1
                prev_tag   = None
                prev_cate  = None

        char_idx += len(word)

    if prev_cate is not None:
        len_sen = len(''.join([w for w in words]))
        spans.append((span_begin, len_sen, prev_cate))

    return spans
