# example:
MODEL_NAME="ja_ginza_electra"
INPUT_DOCBIN=data/processed/sample_ja_ner/spacy/all.spacy
LABEL_CONV_MAP=data/supplement/label_map/labelmap_ene-v7.1.0_to_loc-fac-org-name.json

poetry run python ent_tools/nlp_tools/spacy/evaluate.py \
       -m $MODEL_NAME \
       -i $INPUT_DOCBIN \
       -l $LABEL_CONV_MAP
