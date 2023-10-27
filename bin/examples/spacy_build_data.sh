# example:
MODEL_NAME="ja_ginza_electra"
INPUT_JSON=data/processed/sample_ja_ner/json/all.json
OUTPUT_DOCBIN=data/processed/sample_ja_ner/spacy/all.spacy

python src/nlp_tools/spacy/json_to_docbin.py \
       -m $MODEL_NAME \
       -i $INPUT_JSON \
       -o $OUTPUT_DOCBIN
