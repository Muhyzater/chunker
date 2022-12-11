import os
import sys

from utterance_segmentation.chunker import Chunker
from utterance_segmentation.rpc.utterance_segmentation_pb2_grpc import utterance_segmentationServicer as BaseServicer
from . import AbortableRPC
import utterance_segmentation.rpc.utterance_segmentation_pb2 as uspb2
import grpc
from utterance_segmentation.utils import (
    remove_tag,
    sentence_length,
    seperate_on_sentence,
    validate_ssml,
)


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



class USServicer(BaseServicer, metaclass=AbortableRPC):
    def __init__(self, configs):

        self.configs = configs
        self.chunker = Chunker(
        self.configs["chunker_lm_path"],
        self.configs["max_words_per_sentence"],
        self.configs["split_by_punctuation"],
        self.configs["max_total_words"],
    )

    def chunk(self, request: uspb2.USRequest, context):
        if not request.segmenter_type:
            request.segmenter_type = "lm"
        if request.parse_ssml:
            verdict = validate_ssml(request.text)
            if not verdict.is_valid:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT,  verdict.reason)
            text = remove_tag(request.text, "speak")
            sentences = seperate_on_sentence(text)
            results = []
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence_length(sentence) > self.configs["max_words_per_sentence"]:
                    chunks = self.chunker.run(
                        text=sentence, segmenter_type=request.segmenter_type
                    )
                    results.extend(chunks)
                else:
                    results.append(sentence)
            result = [chunk for chunk in results if chunk]
        else:
            result = self.chunker.run(request.text,segmenter_type=request.segmenter_type)
        response = uspb2.USResponse(text=result)
        return response
