# example:
MODEL_NAME="ja_ginza_electra"
INPUT_DOCBIN=data/processed/sample_ja_ner/spacy/all.spacy
OUTPUT_JSON=data/output/sample_ja_ner/spacy/ja_ginza_electra/json/all.json

python src/nlp_tools/spacy/decode.py \
       -m $MODEL_NAME \
       -i $INPUT_DOCBIN \
       -o $OUTPUT_JSON
