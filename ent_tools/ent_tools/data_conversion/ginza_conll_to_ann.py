import argparse

from logzero import logger

from ent_tools.util.constants import NON_ENTITY
from ent_tools.util.data_io import load_json
from ent_tools.data_conversion.util import read_tsv, get_spans_from_BIO_seq


def read_and_write(
        conll_path: str,
        output_ann_path: str,
        tsv_path: str = None,
        labelmap: dict = None,
) -> None:

    sen = None
    words = []
    labels = []

    men_id = 1
    sen_begin_global = 0
    
    tsv_reader = read_tsv(tsv_path) if tsv_path else None

    with open(conll_path) as f, open(output_ann_path, 'w') as fw:
        logger.info(f'Read: {conll_path}')
        for line in f:
            line = line.rstrip('\n')

            if line.startswith('#'):
                continue

            elif not line:
                sen = ''.join(words)

                if tsv_reader:
                    sen_begin_global, sen_tsv = tsv_reader.__next__()
                    assert sen == sen_tsv

                spans = get_spans_from_BIO_seq(words, labels)
                for span in spans:
                    begin = span[0]
                    end   = span[1]
                    label = span[2]
                    if labelmap:
                        if label in labelmap:
                            label = labelmap[label]
                        else:
                            continue

                    if sen[end-1] == '　':
                        end -= 1

                    span_text = sen[begin:end]

                    begin_global = sen_begin_global + begin
                    end_global   = sen_begin_global + end
                    fw.write(f'T{men_id}\t{label} {begin_global} {end_global}\t{span_text}\n')
                    men_id += 1

                sen = None
                words = []
                labels = []
                
            else:
                array = line.split('\t')
                word  = array[1]
                attrs = array[9].split('|')
                ene   = NON_ENTITY
                space_after = False
                for attr in attrs:
                    if attr == 'SpaceAfter=Yes':
                        space_after = True
                    elif attr.startswith('ENE'):
                        ene = attr[4:]

                words.append(word)
                labels.append(ene)

                if space_after:
                    words.append(' ')
                    labels.append(NON_ENTITY)

        logger.info(f'Save: {output_ann_path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_conll', '-conll',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--tsv_with_text_span', '-tsv',
        type=str,
        dest='tsv',
    )
    parser.add_argument(
        '--output_ann', '-ann',
        type=str,
        required=True,
    )
    parser.add_argument(
        '--label_conversion_map_path', '-label',
        type=str,
    )
    args = parser.parse_args()
    
    labelmap = None
    if args.label_conversion_map_path:
        labelmap = load_json(args.label_conversion_map_path)

    read_and_write(args.input_conll, args.output_ann,
                   tsv_path=args.tsv,
                   labelmap=labelmap)


if __name__ == '__main__':
    main()
