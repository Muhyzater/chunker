if [[ $M3_chunker_lm_path == s3://* ]]
then
    M3_chunker_lm_path_local=$(echo $M3_chunker_lm_path | rev | cut -d "/" -f 1 | rev)
    if [ ! -f "utterance_segmentation/models/$M3_chunker_lm_path_local" ]
    then
        aws s3 cp "$M3_chunker_lm_path" "utterance_segmentation/models/"
    fi
    M3_chunker_lm_path="utterance_segmentation/models/$M3_chunker_lm_path_local"
fi

python3 utterance_segmentation/api.py
