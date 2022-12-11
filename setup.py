from codecs import open
from os import path

from setuptools import find_packages, setup

setup(
    name="utterance_segmentation",
    version="v1.1.9",
    description="Utterance Segmentation Microservice",
    author="Qusai Abu-Obaida",
    author_email="qusai.abuobaida@mawdoo3.com",
    license="Proprietary: Mawdoo3 internal use only",
    classifiers=[
        "Environment :: console",
        "Intended Audience :: Developers",
        "Natural Language :: Arabic",
        "Operating System :: OS Independent",
        "Programming Language :: Python 3.6",
        "Topic :: Utilities",
    ],
    keywords="nlp tts arabic_language segmentation",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=[
        "grpcio",
        "grpcio-health-checking==1.29",
        "grpcio-reflection==1.29"
],
    test_suite="nose2.collector.collector",
    extras_require={
        "test": ["nose2"],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "mawdoo3-utterance-segmentation=utterance_segmentation.api:run",
        ],
    },
)
