# Set paths
GOLD_JSON=
PRED_JSON=
LABEL_CONVERSION_MAP=
SCORE_JSON=

python src/evaluate/evaluate_mention_recognition.py \
       -g $GOLD_JSON \
       -p $PRED_JSON \
       -l $LABEL_CONVERSION_MAP \
       -s $SCORE_JSON
