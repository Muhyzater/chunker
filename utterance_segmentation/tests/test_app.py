import json

import requests
from micro_service.micro_service_test_class import MicroServiceTestClass
from utterance_segmentation.api import chunker_service


class ChunkerTest(MicroServiceTestClass):
    with open("utterance_segmentation/tests/test_cases.json") as f:
        test_cases = json.load(f)

    link_chunker = "http://localhost:5000/chunker"

    @classmethod
    def setUpClass(self):
        app = chunker_service(run=False)
        super(ChunkerTest, self).setUpClass(
            app,
            title="Utterance Segmentation",
            description=(
                "utterance segmenter Microservice developed to "
                "segment long texts into meaningful chunks, "
                "returns the segmented parts of the text"
            ),
        )

    def test_bad_request(self):
        """
        Implements a test for a bad request case; missing "sentence" field
        """

        response = requests.post(self.link_chunker, json={})
        self.assertEqual(response.status_code, 400)

    def test_not_found_url(self):
        """
        Implements a test for a not-found-url request case
        """

        response = requests.post(
            self.link_chunker + "x",
            json={
                "text": self.test_cases["lm"]["input"],
                "segmenter_type": "lm",
                "parse_ssml": False,
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_english(self):
        """
        Implement a test to check if the API doesn't fail when text has
        English words
        """

        response = requests.post(
            self.link_chunker,
            json={"text": self.test_cases["english"]["input"], "segmenter_type": "lm"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)

    def test_chunker_lm(self):

        response = requests.post(
            self.link_chunker,
            json={"text": self.test_cases["lm"]["input"], "segmenter_type": "lm"},
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()["results"]
        self.assertEqual(result, self.test_cases["lm"]["output"])


    def test_chunker_max(self):

        response = requests.post(
            self.link_chunker,
            json={"text": self.test_cases["max"]["input"], "segmenter_type": "max"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()["results"]

        self.assertEqual(result, self.test_cases["max"]["output"])

    def test_chunker_default(self):
        """
        test that `segmenter_type` defaults to `lm`
        """

        response = requests.post(
            self.link_chunker, json={"text": self.test_cases["lm"]["input"]}
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()["results"]
        self.assertEqual(result, self.test_cases["lm"]["output"])

    def test_ssml(self):
        """
        test SSML support
        """

        response = requests.post(
            self.link_chunker,
            json={"text": self.test_cases["ssml"]["input"], "parse_ssml": True},
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()["results"]
        self.assertEqual(result, self.test_cases["ssml"]["output"])

    def test_ssml_validation(self):
        """
        test SSML validation
        """

        # valid SSML
        response = requests.post(
            self.link_chunker,
            json={"text": self.test_cases["ssml"]["input"], "parse_ssml": True},
        )

        self.assertEqual(response.status_code, 200)

        # invalid SSML
        for test_case in self.test_cases["ssml_validation"]:

            response = requests.post(
                self.link_chunker,
                json={"text": test_case["input"], "parse_ssml": True},
            )

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["results"], test_case["output"])

    def test_generate_openapi(self):
        """
        generating OpenAPI doc
        """

        # request with all params
        response = requests.post(
            self.link_chunker,
            params={
                "text": self.test_cases["lm"]["input"],
                "segmenter_type": "lm",
                "parse_ssml": False,
            },
        )

        desc = (
            "segment `text` using selected segmentor type, "
            " possible values `lm` and `max` "
            "or segment  using SSML rules if `parse_ssml` is `True`"
        )

        self.assertEqual(response.status_code, 200)
        self.add_documentation(response, desc)

        # request with required only
        response = requests.post(
            self.link_chunker,
            params={"text": self.test_cases["lm"]["input"]},
        )
        self.assertEqual(response.status_code, 200)
        self.add_documentation(response, desc)
