import re

import kenlm
import requests
from arabic_analysis import arabic as ar
from flask import current_app, g


class Chunker(object):
    def __init__(
        self,
        language_model_path,
        max_words_per_sentence,
        split_by_punctuation,
        max_total_words,
    ):

        self.TASHKEEL_TATWEEL_DICT = {
            ord(x): None
            for x in set(ar.ARABIC_TATWEEL) | ar.ARABIC_EXTENDED_TASHKEEL
            if x != " "
        }
        self.AR_CHARS = (
            {" "}
            | ar.ARABIC_CHARS
            | set(ar.ARABIC_TATWEEL)
            | ar.ARABIC_EXTENDED_TASHKEEL
        )

        self.language_model = kenlm.LanguageModel(language_model_path)
        self.max_words = max_words_per_sentence
        self.split_by_punctuation = split_by_punctuation
        self.max_total_words = max_total_words
        self.puncs = re.escape(
            "".join(list(ar.ARABIC_PUNC) + ["?", ";", "-", "\n", "@", "#", "$", "="])
        )


    def score(self, words):
        # Join words
        text = " ".join(words)
        # Normalize encoding
        normalized = ar.normalize_encoding(text, normalize_combined=True)
        # Remove Tashkeel and Tatweel
        normalized = normalized.translate(self.TASHKEEL_TATWEEL_DICT)
        # Keep only Arabic characters
        normalized = re.sub(
            " +",
            " ",
            "".join([ch if ch in self.AR_CHARS else " " for ch in normalized]),
        )
        # Return language model score
        score = self.language_model.score(normalized)
        return score

    def __lm_chunk_utterance(self, text):
        """
        Implementation for a dynamic programming chunker based on a language model
        to chunk while maximizing the sum of chunks scores
        """
        words = text.split()
        # If text is already short enough, do not split
        if len(words) <= self.max_words:
            chunks = words
        else:
            # Create dynamic programming arrays
            optimal = [float("-inf")] * len(words)
            track = [-1] * len(words)
            # Initialize base cases
            for j in range(self.max_words):
                if j >= len(words):
                    break
                optimal[j] = self.score(words[: j + 1])
            # Find optimal solution
            for i in range(len(words)):
                for j in range(1, self.max_words + 1):
                    if i + j >= len(words):
                        break
                    new_optimal = optimal[i] + self.score(words[i + 1: i + j + 1])
                    if optimal[i + j] < new_optimal:
                        optimal[i + j] = new_optimal
                        track[i + j] = i
            # Track optimal solution path
            solution = [len(words)]
            prev_track = track[-1]
            while prev_track != -1:
                solution.append(prev_track)
                prev_track = track[prev_track]
            chunks = []
            idx = 0
            for i in reversed(solution):
                chunks.append(words[idx: i + 1])
                idx = i + 1
        return chunks

    def __is_last_punc(self, sentence):
        return (
            len(sentence) > 0
            and len(sentence[-1]) > 0
            and sentence[-1][-1] in ar.ARABIC_PUNC
        )

    def run(self, text, segmenter_type):
        chunks = []
        # Split text by punctuation
        chunk = ""
        if self.split_by_punctuation:
            for ch in text:
                chunk += ch
                if ch in ar.ARABIC_PUNC:
                    chunks.append(chunk.strip())
                    chunk = ""
            if len(chunk) > 0:
                chunks.append(chunk)
        else:
            chunks = [text]

        # Chunk depending on the segmenter type
        new_chunks = []
        for chunk in chunks:
            if segmenter_type == "lm" and len(chunk.split()) > self.max_words:
                new_chunks.extend(self.__lm_chunk_utterance(chunk))
            else:
                new_chunks.extend([[w] for w in chunk.split()])
        chunks = new_chunks

        # Merge consecutive sentences if too short
        sentences = []
        sentence = []
        total_words = 0
        for chunk in chunks:
            # If reached max total words, break
            if total_words + len(chunk) > self.max_total_words:
                break
            total_words += len(chunk)

            # If adding this chunk exceeds max sentence length
            # or the sentence has punctuation at the end
            # then start a new sentence
            if len(sentence) + len(chunk) > self.max_words or (
                self.split_by_punctuation and self.__is_last_punc(sentence)
            ):
                sentences.append(sentence)
                sentence = []
            # Add chunk to the current sentence
            sentence += chunk

        # Add last sentence if not empty
        if total_words <= self.max_total_words and len(sentence) > 0:
            sentences.append(sentence)

        all_chunks = []
        for words in sentences:
            sentence = " ".join(words)
            # Skip of empty sentence
            if not sentence:
                continue
            # Skip if the whole sentence is punctuation
            is_all_punc = True
            for ch in sentence:
                if ch not in ar.ARABIC_PUNC:
                    is_all_punc = False
                    break
            if is_all_punc:
                continue

            # If not splitting by punctuation,
            # remove muliple punctuations (keep first one)
            if not self.split_by_punctuation:
                # Replace sequence of puncs with the first punc
                sentence = re.sub(
                    r"([%s])[%s]+" % (self.puncs, self.puncs + " "), r" \1 ", sentence
                )
                # Remove multiple whitespaces
                sentence = re.sub(" +", " ", sentence)

            if sentence:
                all_chunks.append(sentence)

        return all_chunks
