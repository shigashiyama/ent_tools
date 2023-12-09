import argparse
import unicodedata

from logzero import logger


def normalize(
        text: str
) -> str:

    text = unicodedata.normalize('NFKC', text)
    text = text.replace(' ', '　')
    return text


def read_and_write(
        input_txt: str,
        output_tsv: str,
        output_txt: str = None,
        do_normalization: bool = False,
) -> None:

    line_info_list = []
    bol_idx = 0                 # begin of line

    with open(input_txt) as f:
        logger.info(f'Read: {input_txt}')
        for line_num, line in enumerate(f):
            
            text = normalize(line) if do_normalization else line
            text_begin = 0
            text_end = len(text)

            text_begin_global = bol_idx + text_begin
            text_end_global   = bol_idx + text_end
                
            line_info = (line_num+1, line, text_begin_global, text_end_global, text)
            line_info_list.append(line_info)
            bol_idx += len(line)
    
    with open(output_tsv, 'w') as fw_tsv:
        if output_txt:
            fw_txt = open(output_txt, 'w')

        men_id = 1
        for line_info in line_info_list:
            line_num, line, begin, end, text = line_info
            fw_tsv.write(f'{line_num}\t{begin}\t{end}\t{text}')
            if output_txt:
                fw_txt.write(line)

        logger.info(f'Save: {output_tsv}')
        if output_txt:
            fw_txt.close()
            logger.info(f'Save: {output_txt}')


# TSV file with raw sentences and span info are generated from input TXT file,
# for applying pre-annotation using NER system (e.g., GiNZA).
# TXT file performed with character normalization is saved as TXT file for Brat.
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_txt', '-itxt', default='', required=True)
    parser.add_argument('--output_tsv', '-tsv', default='', required=True)
    parser.add_argument('--output_txt', '-otxt', default='')
    parser.add_argument('--nfkc_normalize', '-nfkc', action='store_true')

    args = parser.parse_args()
    read_and_write(args.input_txt, args.output_tsv, args.output_txt, 
                   do_normalization=args.nfkc_normalize)


if __name__ == '__main__':
    main()
