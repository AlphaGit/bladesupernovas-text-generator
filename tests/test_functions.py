# -*- coding: utf-8 -*-

from text_generator.functions import lower_bound, upper_bound

import unittest

class LowerBoundTestSuite(unittest.TestCase):
    """lower_bound test cases."""

    def test_returns_0_when_list_is_empty(self):
        self.assertEqual(lower_bound([], 'a'), 0)
        self.assertEqual(lower_bound([], 'b'), 0)
        self.assertEqual(lower_bound([], '1'), 0)
        self.assertEqual(lower_bound([], 'alpha'), 0)

    def test_identifies_index_in_the_middle_of_list(self):
        self.assertEqual(lower_bound(['alpha', 'beta', 'charlie'], 'blue'), 2) # blue > alpha and blue > beta

    def test_considers_words_ordered_alphabetically(self):
        self.assertEqual(lower_bound(['aa', 'ab'], 'ac'), 2)
        self.assertEqual(lower_bound(['alpha', 'charlie'], 'blue'), 1)

    def test_returns_first_index_when_several_items_are_equal(self):
        self.assertEqual(lower_bound(['a'], 'a'), 0)
        self.assertEqual(lower_bound(['a', 'b'], 'b'), 1)
        self.assertEqual(lower_bound(['a', 'c', 'd', 'd'], 'd'), 2)

    def test_returns_list_size_when_item_is_higher_than_all(self):
        self.assertEqual(lower_bound(['b'], 'c'), 1)
        self.assertEqual(lower_bound(['blue', 'charlie', 'definitive'], 'zulu'), 3)

    def test_considers_hi_as_maximum_value(self):
        self.assertEqual(lower_bound(['aa', 'ab'], 'ac', hi=1), 1)
        self.assertEqual(lower_bound(['alpha', 'beta', 'charlie'], 'blue', hi=1), 1)

        self.assertEqual(lower_bound(['blue', 'charlie', 'definitive'], 'zulu'), 3)
        self.assertEqual(lower_bound(['blue', 'charlie', 'definitive'], 'zulu', hi=2), 2)
        self.assertEqual(lower_bound(['blue', 'charlie', 'definitive'], 'zulu', hi=1), 1)
        self.assertEqual(lower_bound(['blue', 'charlie', 'definitive'], 'zulu', hi=0), 0)

    def test_considers_lo_as_minimum_value(self):
        self.assertEqual(lower_bound([], 'a', lo=1), 1)
        self.assertEqual(lower_bound([], 'a', lo=2), 2)
        self.assertEqual(lower_bound([], 'a', lo=3), 3)

        self.assertEqual(lower_bound(['aa', 'ab'], 'ac'), 2)
        self.assertEqual(lower_bound(['aa', 'ab'], 'ac', lo=1), 2)
        self.assertEqual(lower_bound(['aa', 'ab'], 'ac', lo=2), 2)
        self.assertEqual(lower_bound(['aa', 'ab'], 'ac', lo=3), 3)
        self.assertEqual(lower_bound(['aa', 'ab'], 'ac', lo=4), 4)

    def test_raises_if_lo_is_less_than_zero(self):
        with self.assertRaises(ValueError):
            lower_bound([], 'a', lo=-1)

        with self.assertRaises(ValueError):
            lower_bound([], 'a', lo=-2)

    def test_raises_if_hi_is_bigger_than_length_of_array(self):
        with self.assertRaises(ValueError):
            lower_bound([], 'a', hi=1)

        with self.assertRaises(ValueError):
            lower_bound(['a'], 'b', hi=2)

class UpperBoundTestSuite(unittest.TestCase):
    """upper_bound test cases."""

    def test_returns_0_when_list_is_empty(self):
        self.assertEqual(upper_bound([], 'a'), 0)
        self.assertEqual(upper_bound([], 'b'), 0)
        self.assertEqual(upper_bound([], '1'), 0)
        self.assertEqual(upper_bound([], 'alpha'), 0)

    def test_identifies_index_in_the_middle_of_list(self):
        self.assertEqual(upper_bound(['alpha', 'beta', 'charlie'], 'blue'), 2) # blue > alpha and blue > beta

    def test_considers_words_ordered_alphabetically(self):
        self.assertEqual(upper_bound(['aa', 'ab'], 'ac'), 2)
        self.assertEqual(upper_bound(['alpha', 'charlie'], 'blue'), 1)

    def test_returns_last_index_when_several_items_are_equal(self):
        self.assertEqual(upper_bound(['a'], 'a'), 1)
        self.assertEqual(upper_bound(['a', 'b'], 'b'), 2)
        self.assertEqual(upper_bound(['a', 'c', 'd', 'd'], 'd'), 4)

    def test_returns_list_size_when_item_is_higher_than_all(self):
        self.assertEqual(upper_bound(['b'], 'c'), 1)
        self.assertEqual(upper_bound(['blue', 'charlie', 'definitive'], 'zulu'), 3)

    def test_considers_hi_as_maximum_value(self):
        self.assertEqual(upper_bound(['aa', 'ab'], 'ac', hi=1), 1)
        self.assertEqual(upper_bound(['alpha', 'beta', 'charlie'], 'blue', hi=1), 1)

        self.assertEqual(upper_bound(['blue', 'charlie', 'definitive'], 'zulu'), 3)
        self.assertEqual(upper_bound(['blue', 'charlie', 'definitive'], 'zulu', hi=2), 2)
        self.assertEqual(upper_bound(['blue', 'charlie', 'definitive'], 'zulu', hi=1), 1)
        self.assertEqual(upper_bound(['blue', 'charlie', 'definitive'], 'zulu', hi=0), 0)

    def test_considers_lo_as_minimum_value(self):
        self.assertEqual(upper_bound([], 'a', lo=1), 1)
        self.assertEqual(upper_bound([], 'a', lo=2), 2)
        self.assertEqual(upper_bound([], 'a', lo=3), 3)

        self.assertEqual(upper_bound(['aa', 'ab'], 'ac'), 2)
        self.assertEqual(upper_bound(['aa', 'ab'], 'ac', lo=1), 2)
        self.assertEqual(upper_bound(['aa', 'ab'], 'ac', lo=2), 2)
        self.assertEqual(upper_bound(['aa', 'ab'], 'ac', lo=3), 3)
        self.assertEqual(upper_bound(['aa', 'ab'], 'ac', lo=4), 4)

    def test_raises_if_lo_is_less_than_zero(self):
        with self.assertRaises(ValueError):
            upper_bound([], 'a', lo=-1)

        with self.assertRaises(ValueError):
            upper_bound([], 'a', lo=-2)

    def test_raises_if_hi_is_bigger_than_length_of_array(self):
        with self.assertRaises(ValueError):
            lower_bound([], 'a', hi=1)

        with self.assertRaises(ValueError):
            lower_bound(['a'], 'b', hi=2)

if __name__ == 'main':
    unittest.main()