## Set paths

# gold standard file
GOLD_JSON=

# system output file
PRED_JSON=

# label conversion map (c.f. data/supplement/label_map/*.json)
LABEL_CONVERSION_MAP=

# file to output scores
SCORE_JSON=

poetry run python ent_tools/evaluate/evaluate_mention_recognition.py \
       -g $GOLD_JSON \
       -p $PRED_JSON \
       -l $LABEL_CONVERSION_MAP \
       -s $SCORE_JSON
