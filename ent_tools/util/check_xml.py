import argparse
import xml
import xml.etree.ElementTree as ET

from logzero import logger


def check_xml(input_xml):
    try:
        logger.info(f'Check: {input_xml}')
        tree = ET.parse(input_xml)
        
    except xml.etree.ElementTree.ParseError as e:
        e_line_num, e_col_num = e.position
        e_line = None
        with open(input_xml) as f:
            for i, line in enumerate(f):
                if i == e_line_num:
                   e_line = line.rstrip('\n')
                   break
        logger.error(f'Exception: {e}; char="{e_line[e_col_num]}"; line="{e_line}"')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_xml', '-xml',
        type=str,
        required=True,
    )
    args = parser.parse_args()
    check_xml(args.input_xml)


if __name__ == '__main__':
    main()
