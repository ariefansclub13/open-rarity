import time
from random import sample

import numpy as np
import pytest

from open_rarity.scoring.handlers.arithmetic_mean_scoring_handler import (
    ArithmeticMeanScoringHandler,
)
from open_rarity.scoring.handlers.geometric_mean_scoring_handler import (
    GeometricMeanScoringHandler,
)
from open_rarity.scoring.handlers.harmonic_mean_scoring_handler import (
    HarmonicMeanScoringHandler,
)
from open_rarity.scoring.handlers.information_content_scoring_handler import (
    InformationContentScoringHandler,
)
from open_rarity.scoring.utils import get_token_attributes_scores_and_weights
from tests.helpers import (
    generate_collection_with_token_traits,
    generate_mixed_collection,
    generate_onerare_rarity_collection,
    generate_uniform_rarity_collection,
    get_mixed_trait_spread,
)


class TestScoringHandlers:
    max_scoring_time_for_10k_s = 2

    uniform_collection = generate_uniform_rarity_collection(
        attribute_count=5,
        values_per_attribute=10,
        token_total_supply=10000,
    )

    # The last token (#9999) has a unique attribute value for all
    # 5 different attribute types
    onerare_collection = generate_onerare_rarity_collection(
        attribute_count=5,
        values_per_attribute=10,
        token_total_supply=10000,
    )

    # Collection with following attribute distribution
    # "hat":
    #   20% have "cap",
    #   30% have "beanie",
    #   45% have "hood",
    #   5% have "visor"
    # "shirt":
    #   80% have "white-t",
    #   20% have "vest"
    # "special":
    #   1% have "special"
    #   others none
    mixed_collection = generate_mixed_collection()

    def test_geometric_mean_scorer_uniform(self) -> None:
        """test the geometric mean implementation of score_token"""
        geometric_mean_rarity = GeometricMeanScoringHandler()
        uniform_tokens_to_test = [
            self.uniform_collection.tokens[0],
            self.uniform_collection.tokens[1405],
            self.uniform_collection.tokens[9999],
        ]
        expected_uniform_score = 10.0
        for token_to_test in uniform_tokens_to_test:
            assert np.round(
                geometric_mean_rarity.score_token(
                    collection=self.uniform_collection, token=token_to_test
                ),
                12,
            ) == np.round(expected_uniform_score, 12)

    def test_geometric_mean_scorer_onerare(self) -> None:
        geometric_mean_rarity = GeometricMeanScoringHandler()
        common_token = self.onerare_collection.tokens[0]
        # Since weights and scores for every trait will all be the same,
        # the score is just the same as a trait score
        expected_common_score = 10000 / 1111
        assert np.round(
            geometric_mean_rarity.score_token(
                collection=self.onerare_collection, token=common_token
            ),
            8,
        ) == np.round(expected_common_score, 8)

        rare_token = self.onerare_collection.tokens[-1]
        # Since weights and scores for every trait will all be the same,
        # the score is just the same as a trait score
        expected_rare_score = 10000
        assert np.round(
            geometric_mean_rarity.score_token(
                collection=self.onerare_collection, token=rare_token
            ),
            8,
        ) == np.round(expected_rare_score, 8)

    @pytest.mark.skip(reason="Not including performance testing as required testing")
    def test_arithmetic_mean_score_collection_timing(self) -> None:
        arithmetic_scorer = ArithmeticMeanScoringHandler()
        tic = time.time()
        arithmetic_scorer.score_tokens(
            collection=self.mixed_collection,
            tokens=self.mixed_collection.tokens,
        )
        toc = time.time()
        assert (toc - tic) < self.max_scoring_time_for_10k_s

    def test_arithmetic_mean_uniform(self) -> None:
        """test the arithmetic mean implementation of score_token"""
        arithmetic_mean_rarity = ArithmeticMeanScoringHandler()
        tokens_to_test = [
            self.uniform_collection.tokens[0],
            self.uniform_collection.tokens[1],
            self.uniform_collection.tokens[4050],
            self.uniform_collection.tokens[9998],
        ]
        expected_score = 10

        for token in tokens_to_test:
            assert np.round(
                arithmetic_mean_rarity.score_token(
                    collection=self.uniform_collection, token=token
                ),
                8,
            ) == np.round(expected_score, 8)

    def test_arithmetic_mean_mixed(self) -> None:
        arithmetic_scorer = ArithmeticMeanScoringHandler()
        token_idxs_to_test = sample(range(self.mixed_collection.token_total_supply), 20)
        scores = arithmetic_scorer.score_tokens(
            collection=self.mixed_collection,
            tokens=self.mixed_collection.tokens,
        )
        assert len(scores) == 10000
        for token_idx in token_idxs_to_test:
            token = self.mixed_collection.tokens[token_idx]
            score = scores[token_idx]
            assert score == arithmetic_scorer.score_token(
                collection=self.mixed_collection,
                token=token,
            )
            trait_scores, weights = get_token_attributes_scores_and_weights(
                collection=self.mixed_collection,
                token=token,
                normalized=True,
            )
            assert np.average(trait_scores, weights=weights) == score

    def test_harmonic_mean_uniform(self) -> None:
        """test the harmonic mean implementation of score_token"""
        harmonic_mean_rarity = HarmonicMeanScoringHandler()

        uniform_token_to_test = self.uniform_collection.tokens[0]
        uniform_harmonic_mean = 10
        assert np.round(
            harmonic_mean_rarity.score_token(
                collection=self.uniform_collection, token=uniform_token_to_test
            ),
            8,
        ) == np.round(uniform_harmonic_mean, 8)

    def test_information_content_rarity_uniform(self):
        information_content_rarity = InformationContentScoringHandler()

        uniform_token_to_test = self.uniform_collection.tokens[0]
        uniform_ic_rarity = 1.0
        assert np.round(
            information_content_rarity.score_token(
                collection=self.uniform_collection, token=uniform_token_to_test
            ),
            8,
        ) == np.round(uniform_ic_rarity, 8)

    def test_information_content_rarity_mixed(self):
        ic_scorer = InformationContentScoringHandler()

        # First test collection entropy
        collection_entropy = ic_scorer._get_collection_entropy(self.mixed_collection)
        collection_probs = []
        mixed_spread = get_mixed_trait_spread()
        for trait_dict in mixed_spread.values():
            for tokens_with_trait in trait_dict.values():
                collection_probs.append(tokens_with_trait / 10000)

        assert np.round(collection_entropy, 10) == np.round(
            -np.dot(collection_probs, np.log2(collection_probs)), 10
        )

        # Test the actual scores
        token_idxs_to_test = sample(range(self.mixed_collection.token_total_supply), 20)
        scores = ic_scorer.score_tokens(
            collection=self.mixed_collection,
            tokens=self.mixed_collection.tokens,
        )
        assert len(scores) == 10000
        for token_idx in token_idxs_to_test:
            token = self.mixed_collection.tokens[token_idx]
            score = scores[token_idx]
            assert score == ic_scorer.score_token(
                collection=self.mixed_collection,
                token=token,
            )
            attr_scores, _ = get_token_attributes_scores_and_weights(
                collection=self.mixed_collection,
                token=token,
                normalized=True,
            )
            ic_token_score = -np.sum(np.log2(np.reciprocal(attr_scores)))

            assert score == ic_token_score / collection_entropy

    def test_information_content_null_attribute(self):
        collection_with_null = generate_collection_with_token_traits(
            [
                {"bottom": "1", "hat": "1", "special": "true"},
                {"bottom": "1", "hat": "1"},
                {"bottom": "2", "hat": "2"},
                {"bottom": "2", "hat": "2"},
                {"bottom": "3", "hat": "2"},
            ]
        )

        collection_without_null = generate_collection_with_token_traits(
            [
                {"bottom": "1", "hat": "1", "special": "true"},
                {"bottom": "1", "hat": "1", "special": "false"},
                {"bottom": "2", "hat": "2", "special": "false"},
                {"bottom": "2", "hat": "2", "special": "false"},
                {"bottom": "3", "hat": "2", "special": "false"},
            ]
        )

        ic_scorer = InformationContentScoringHandler()

        scores_with_null = ic_scorer.score_tokens(
            collection=collection_with_null, tokens=collection_with_null.tokens
        )
        scores_without_null = ic_scorer.score_tokens(
            collection=collection_without_null,
            tokens=collection_without_null.tokens,
        )

        assert scores_with_null == scores_without_null

    @pytest.mark.skip(reason="Not including performance testing as required testing")
    def test_information_content_rarity_timing(self):
        ic_scorer = InformationContentScoringHandler()
        tic = time.time()
        ic_scorer.score_tokens(
            collection=self.mixed_collection,
            tokens=self.mixed_collection.tokens,
        )
        toc = time.time()
        assert (toc - tic) < self.max_scoring_time_for_10k_s
