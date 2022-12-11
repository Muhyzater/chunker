import os
import sys
from traceback import print_exc

from config import config
from concurrent import futures
import grpc
from flask import g
from grpc_health.v1.health import HealthServicer
from grpc_health.v1.health_pb2 import DESCRIPTOR as health_Descriptor
from grpc_health.v1.health_pb2_grpc import add_HealthServicer_to_server
from grpc_reflection.v1alpha import reflection
from micro_service import MicroService, Param, ParamSources, get_blueprint
import utterance_segmentation.rpc.utterance_segmentation_servicer as US
import utterance_segmentation.rpc.utterance_segmentation_pb2 as uspb2
import utterance_segmentation.rpc.utterance_segmentation_pb2_grpc as uspb2_grpc


from utterance_segmentation.chunker import Chunker
from utterance_segmentation.utils import (
    remove_tag,
    sentence_length,
    seperate_on_sentence,
    validate_ssml,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.getcwd()))

blueprint = get_blueprint()
model = None


def create_RPC_service(**kwargs):
    params = config
    params.update(kwargs)

    server_info = (
        uspb2.DESCRIPTOR.services_by_name["utterance_segmentation"].full_name,
        health_Descriptor.services_by_name["Health"].full_name,
        reflection.SERVICE_NAME,
    )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=params["workers"]))

    servicer = US.USServicer(config)

    uspb2_grpc.add_utterance_segmentationServicer_to_server(servicer, server)
    add_HealthServicer_to_server(HealthServicer(), server)
    server.add_insecure_port("0.0.0.0:{}".format(params["port"]))
    reflection.enable_server_reflection(server_info, server)

    return server


def chunker_service(run=False, **kwargs):

    params = config
    params.update(kwargs)
    chunker_micro_service = MicroService(__name__, **params)
    chunker_micro_service.register_blueprint(blueprint)

    # get config of ms
    ms_config = chunker_micro_service.config

    # initalize chunker
    global model
    model = Chunker(
#        ms_config["ner_url"],
        ms_config["chunker_lm_path"],
        ms_config["max_words_per_sentence"],
        ms_config["split_by_punctuation"],
        ms_config["max_total_words"],
    )

    if run:
        chunker_micro_service.run_service()
    else:
        return chunker_micro_service


@blueprint.route(
    "/chunker",
    methods=["GET", "POST"],
    params=[
        Param(
            name="text",
            type=str,
            required=True,
            source=[ParamSources.ARGS, ParamSources.BODY_JSON],
        ),
        Param(
            name="segmenter_type",
            type=str,
            default="lm",
            source=[ParamSources.ARGS, ParamSources.BODY_JSON],
        ),
        Param(
            name="parse_ssml",
            type=bool,
            default=False,
            source=[ParamSources.ARGS, ParamSources.BODY_JSON],
        ),
    ],
)
def chunker_endpoint():

    cfg = g.config
    p = g.params

    try:
        if p["parse_ssml"]:

            verdict = validate_ssml(p["text"])
            if not verdict.is_valid:
                return verdict.reason, 400

            text = remove_tag(p["text"], "speak")
            sentences = seperate_on_sentence(text)
            results = []

            for sentence in sentences:
                sentence = sentence.strip()

                if sentence_length(sentence) > cfg["max_words_per_sentence"]:

                    chunks = model.run(
                        text=sentence, segmenter_type=p["segmenter_type"]
                    )

                    results.extend(chunks)

                else:
                    results.append(sentence)

            results = [chunk for chunk in results if chunk]

        else:
            results = model.run(text=p["text"], segmenter_type=p["segmenter_type"])

        response = {"status": "SUCCESS", "results": results}

        return response, 200, cfg["headers"]

    except Exception as exception:
        print_exc()
        return "FAIL", 500, cfg["headers"]




def run():
    # do the use_rpc flag.
    if config['use_rpc']:
        service = create_RPC_service()
        service.start()
        print("starting on 0.0.0.0:{}".format(config["port"]))
        service.wait_for_termination()
    else:
        app = chunker_service()
        app.run_service()


if __name__ == "__main__":
    run()
