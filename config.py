import re
import os

_url = "http://yjvhekp74bjkgexwxspeebfb47tqjc.staging.ingress.mawdu.com/{}"
config = dict(
    service_name="utterance_segmentation",
    service_version="v1.1.9",
    environment="dev",
    port=5000,
    file_log=False,
    DEBUG=False,
    gunicorn_workers={"default": 1, "type": int},
    gunicorn_timeout={"default": 200, "type": int},
    chunker_lm_path={"default": "utterance_segmentation/models/lm.bin", "type": str},
    max_words_per_sentence={"default": 10, "type": int},
    split_by_punctuation={"default": True, "type": bool},
    max_total_words={"default": 100, "type": int},
    workers={"default": 10, "type": int},
    use_rpc={"default": True, "type": bool},
)


def get_boolean(value) -> bool:
    t = re.compile(r"^(y|yes|true|on|1)$", re.IGNORECASE)
    f = re.compile(r"^(n|no|false|off|0)$", re.IGNORECASE)

    if t.match(str(value)):
        return True

    elif f.match(str(value)):
        return False
    else:
        raise ValueError("Invalid bool representation: '{}'".format(value))


def update_from_env(config: dict, prefix: str = "M3_", keys: list = None):

    for key in keys or config:
        if type(config[key]) is dict:
            _type = config[key]["type"]
            _default = config[key]["default"]

        else:
            _type = type(config[key])
            _default = config[key]

        config[key] = os.getenv("{}{}".format(prefix, key), _default)

        if _type is bool:
            config[key] = get_boolean(config[key])

        elif _type is not type(None):
            config[key] = _type(config[key])



update_from_env(
    config,
    keys=["use_rpc"],
)
if config["use_rpc"]:
    update_from_env(config)
