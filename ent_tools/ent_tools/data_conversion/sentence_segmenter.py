import argparse
import re

import functools
from ja_sentence_segmenter.split.simple_splitter import split_punctuation


PERIODS = '。！？!?'


class Segmenter(object):
    def __init__(
            self,
            # split_punct: bool = True,
    ):
        self.segmenter = functools.partial(split_punctuation, punctuations=r'。！？!?')
        self.paren_noseg = re.compile(r'(<[^<>]*>)|(【[^【】]*】)|(『[^『』]*』)|(“[^“”]*”)')


    # ja_sentence_segmenter で非対応の括弧表現、連続する同一終端記号に対する処理を補正
    def sentencize(self, text: str) -> list[str]:
        segments = []
     
        matches = list(self.paren_noseg.finditer(text))
        if len(matches) == 0:
            sents = list(self.segmenter(text))
            if len(sents) == 1:
                segments.append(text)
            else:
                segments.extend(adjust_over_segmentation(sents))
     
        else:               # 括弧表現の外部のみ文分割対象
            cur_idx = 0
            for m in matches:
                b_par, e_par = m.span()
     
                # 括弧表現の前方
                if cur_idx < b_par:
                    subtext = text[cur_idx:b_par]
                    subsents = list(self.segmenter(subtext))
     
                    if len(subsents) == 1:
                        segments.append(subtext)
                    else:
                        segments.extend(adjust_over_segmentation(subsents))
     
                # 括弧表現の内部
                segments.append(text[b_par:e_par])
                cur_idx = e_par
     
            # 最後の括弧表現の後方
            if cur_idx < len(text):
                subtext = text[cur_idx:]
                subsents = list(self.segmenter(subtext))
     
                if len(subsents) == 1:
                    segments.append(subtext)
                else:
                    segments.extend(adjust_over_segmentation(subsents))
     
        return segments


def adjust_over_segmentation(texts):
    new_texts = []
    prev_subtext = None
 
    for i, subtext in enumerate(texts):
        # 同一終端記号連続時の補正
        if (prev_subtext
            and prev_subtext[-1] in PERIODS
            and (subtext[0] in PERIODS
                 or subtext[0] in ')）'
            )
        ):
            new_texts[-1] += subtext 
        else:
            new_texts.append(subtext)
 
        prev_subtext = subtext
    
    return new_texts


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--text', required=True)
    args = parser.parse_args()

    segmenter = Segmenter()
    print(segmenter.sentencize(args.text))

