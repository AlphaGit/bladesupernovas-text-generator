# -*- coding: utf-8 -*-

from text_generator.Tree import Tree

import unittest

class TreeBuildTestSuite(unittest.TestCase):
    """Tree.build() test cases."""

    def test_window_size_specifies_amount_of_words_collected_in_each_record(self):
        source_words = ['alpha', 'blue', 'charlie', 'delta']
        tree = Tree(1)
        tree.build(source_words)
        self.assertCountEqual(tree.records, ['alpha', 'blue', 'charlie', 'delta'])

        tree = Tree(2)
        tree.build(source_words)
        self.assertCountEqual(tree.records, ['alpha blue', 'blue charlie', 'charlie delta', 'delta'])

        tree = Tree(3)
        tree.build(source_words)
        self.assertCountEqual(tree.records, ['alpha blue charlie', 'blue charlie delta', 'charlie delta', 'delta'])

        tree = Tree(4)
        tree.build(source_words)
        self.assertCountEqual(tree.records, ['alpha blue charlie delta', 'blue charlie delta', 'charlie delta', 'delta'])

        tree = Tree(5)
        tree.build(source_words)
        self.assertCountEqual(tree.records, ['alpha blue charlie delta', 'blue charlie delta', 'charlie delta', 'delta'])

    def assertListIsSorted(self, listValues):
        previous_value = None
        for index in range(1, len(listValues)):
            previous_value = listValues[index-1]
            current_value = listValues[index]

            self.assertLessEqual(previous_value, current_value)

    def test_words_are_sorted(self):
        tree = Tree(2)
        tree.build(['alpha', 'blue', 'charlie', 'delta'])
        self.assertListIsSorted(tree.records)

        tree = Tree(2)
        tree.build(['alpha', 'zulu', 'blue', 'whisky', 'tango', 'foxtrot', 'charlie', 'delta'])
        self.assertListIsSorted(tree.records)

    def test_words_are_lowercased(self):
        tree = Tree(2)
        tree.build(['Alpha', 'Blue', 'ChArLiE', 'DeltA'])
        for value in tree.records:
            self.assertEqual(value.lower(), value)

    def test_periods_are_allowed_only_at_end_of_word(self):
        tree = Tree(1)
        tree.build(['alpha.', 'bl.ue', '.charlie', 'delta'])

        self.assertCountEqual(['alpha.', 'delta'], tree.records)

    def test_commas_are_allowed_only_at_end_of_word(self):
        tree = Tree(1)
        tree.build(['alpha,', 'bl,ue', ',charlie', 'delta'])

        self.assertCountEqual(['alpha,', 'delta'], tree.records)

    def test_question_marks_are_allowed_only_at_end_of_word(self):
        tree = Tree(1)
        tree.build(['alpha?', 'bl?ue', '?charlie', 'delta'])

        self.assertCountEqual(['alpha?', 'delta'], tree.records)

    def test_exclamation_marks_are_allowed_only_at_end_of_word(self):
        tree = Tree(1)
        tree.build(['alpha!', 'bl!ue', '!charlie', 'delta'])

        self.assertCountEqual(['alpha!', 'delta'], tree.records)

    def test_keeps_track_of_the_amount_of_records(self):
        source_words = ['alpha', 'blue', 'charlie', 'delta']
        tree = Tree(1)
        tree.build(source_words)
        self.assertEqual(4, tree.lenRecords)

        tree = Tree(2)
        tree.build(source_words)
        self.assertEqual(4, tree.lenRecords)

    def test_records_and_length_are_correct_when_no_words_are_accepted(self):
        tree = Tree(1)
        tree.build(['alph!a', 'bl.ue', 'charl1e', 'delt@'])

        self.assertEqual([], tree.records)
        self.assertEqual(0, tree.lenRecords)

class TreeFindIntervalTestSuite(unittest.TestCase):
    """Tree.find_interval() test cases."""

    def test_finds_the_interval_for_a_particular_entry(self):
        tree = Tree(1)
        tree.build(['alpha', 'blue', 'charlie', 'delta'])

        self.assertEqual((0, 0), tree.find_interval('abacus'))
        # alpha
        self.assertEqual((1, 1), tree.find_interval('amaranth'))
        self.assertEqual((1, 1), tree.find_interval('basic'))
        # blue
        self.assertEqual((2, 2), tree.find_interval('buzz'))
        self.assertEqual((2, 2), tree.find_interval('cat'))
        # charlie
        self.assertEqual((3, 3), tree.find_interval('cut'))
        self.assertEqual((3, 3), tree.find_interval('dam'))
        # delta
        self.assertEqual((4, 4), tree.find_interval('during'))

    def test_extends_the_interval_for_repeated_words(self):
        tree = Tree(1)
        tree.build(['alpha', 'alpha', 'blue', 'charlie', 'delta', 'delta'])

        self.assertEqual((0, 2), tree.find_interval('alpha'))
        self.assertEqual((2, 3), tree.find_interval('blue'))
        self.assertEqual((4, 6), tree.find_interval('delta'))

    def test_returns_0_when_no_records(self):
        tree = Tree(1)
        tree.build([])

        self.assertEqual((0, 0), tree.find_interval('alpha'))

class TreeMergeCandidatesTestSuite(unittest.TestCase):
    """Tree.mergeCandidates() test cases."""

    def test_does_nothing_if_no_candidates_are_passed(self):
        tree = Tree(1)
        tree.build(['alpha'])

        self.assertEqual(['alpha'], tree.records)

        tree.mergeCandidates([], 0)

        self.assertEqual(['alpha'], tree.records)

    def test_stores_last_passed_candidates(self):
        tree = Tree(1)
        tree.build(['alpha', 'blue'])

        tree.mergeCandidates([], 0)
        self.assertEqual([], tree.candidates)

        tree.mergeCandidates([(0, 0)], 0)
        self.assertEqual([(0, 0)], tree.candidates)

        tree.mergeCandidates([(1, 1)], 0)
        self.assertEqual([(1, 1)], tree.candidates)

        tree.mergeCandidates([(0, 1)], 0)
        self.assertEqual([(0, 1)], tree.candidates)

        tree.mergeCandidates([], 0)
        self.assertEqual([], tree.candidates)

    def test_candidates_are_sorted(self):
        tree = Tree(1)
        tree.build(['alpha', 'blue', 'charlie', 'delta'])

        tree.mergeCandidates([(1, 1), (0, 0), (2, 2)], 0)
        self.assertEqual([(0, 0), (1, 1), (2, 2)], tree.candidates)

        tree.mergeCandidates([(0, 0), (2, 0), (1, 0)], 0)
        self.assertEqual([(0, 0), (1, 0), (2, 0)], tree.candidates)

    def test_candidates_are_merged_into_the_bigger_range_if_they_share_the_start_index(self):
        tree = Tree(1)
        tree.build(['alpha', 'blue', 'charlie', 'delta'])

        tree.mergeCandidates([(0, 1), (0, 2)], 0)
        self.assertEqual([(0, 2)], tree.candidates)

        tree.mergeCandidates([(1, 1), (1, 4), (2, 3), (2, 5), (1, 5)], 0)
        self.assertEqual([(1, 5), (2, 5)], tree.candidates)

        tree.mergeCandidates([(1, 1), (0, 1), (1, 2), (2, 2), (0, 0)], 0)
        self.assertEqual([(0, 1), (1, 2), (2, 2)], tree.candidates)

    def test_candidates_are_compared_against_the_last(self):
        tree = Tree(1)
        tree.build(['alpha', 'blue', 'charlie', 'delta'])

        tree.mergeCandidates([(3, 3), (4, 4), (2, 2)], 0)
        self.assertEqual([(2, 2), (3, 3), (4, 4)], tree.candidates)

    def test_candidates_are_merged_if_they_contain_the_same_word(self):
        tree = Tree(2)
        tree.build(['alpha', 'blue', 'charlie', 'charlie', 'delta'])

        # records = [
        #   0  'alpha blue',
        #   1  'blue charlie',
        #   2  'charlie charlie',
        #   3  'charlie delta',
        #   4  'delta'
        # ]

        # (2, 2) = ['charlie charlie']
        # (2, 3) = ['charlie charlie', 'charlie delta']
        tree.mergeCandidates([(2, 2), (2, 3)], 1)
        self.assertEqual([(2, 3)], tree.candidates)

        tree.mergeCandidates([(2, 2), (2, 3)], 2)
        self.assertEqual([(2, 2), (2, 2), (2, 3)], tree.candidates)

class TreeUpdateWordsTestSuite(unittest.TestCase):
    """Tree.update_words() test cases."""

    def test_adds_candidates_for_words_between_others(self):
        tree = Tree(2)
        tree.build(['alpha', 'blue', 'charlie', 'charlie', 'delta'])

        # records = [
        #   0  'alpha blue',
        #   1  'blue charlie',
        #   2  'charlie charlie'
        #   3  'charlie delta',
        #   4  'delta'
        # ]

        tree.update_words(0, ['alpha'])
        self.assertEqual([(0, 1)], tree.candidates)

        tree.update_words(0, ['blue'])
        self.assertEqual([(1, 2)], tree.candidates)

        tree.update_words(0, ['charlie'])
        self.assertEqual([(2, 4)], tree.candidates)

    def test_does_nothing_for_not_found_words(self):
        tree = Tree(2)
        tree.build(['alpha', 'blue', 'charlie', 'charlie', 'delta'])

        self.assertEqual([], tree.candidates) 
        unchanged_records = ['alpha blue', 'blue charlie', 'charlie charlie', 'charlie delta', 'delta']
        self.assertEqual(unchanged_records, tree.records)

        tree.update_words(0, ['back'])
        self.assertEqual([], tree.candidates)
        self.assertEqual(unchanged_records, tree.records)

        tree.update_words(1, ['back'])
        self.assertEqual([], tree.candidates)
        self.assertEqual(unchanged_records, tree.records)

        tree.update_words(0, ['alpha blue'])
        self.assertEqual([], tree.candidates)
        self.assertEqual(unchanged_records, tree.records)

        tree.update_words(1, ['alpha blue'])
        self.assertEqual([], tree.candidates)
        self.assertEqual(unchanged_records, tree.records)

    def test_clears_candidates_if_words_do_not_extend_candidates(self):
        tree = Tree(2)
        tree.build(['alpha', 'blue', 'charlie', 'charlie', 'delta'])

        # records = [
        #   0  'alpha blue',
        #   1  'blue charlie',
        #   2  'charlie charlie'
        #   3  'charlie delta',
        #   4  'delta'
        # ]

        tree.update_words(0, ['alpha back'])
        self.assertEqual([], tree.candidates)

        tree.update_words(0, ['alpha alpha'])
        self.assertEqual([], tree.candidates)

        tree.update_words(1, ['alpha back'])
        self.assertEqual([], tree.candidates)

    def test_restricts_candidates_with_further_values_of_word_position(self):
        tree = Tree(3)
        tree.build(['alpha', 'blue', 'charlie', 'charlie', 'delta'])

        # records = [
        #   0  'alpha blue charlie',
        #   1  'blue charlie charlie',
        #   2  'charlie charlie delta'
        #   3  'charlie delta',
        #   4  'delta'
        # ]

        tree.update_words(0, ['charlie'])
        self.assertEqual([(2, 4)], tree.candidates)

        tree.update_words(1, ['charlie'])
        self.assertEqual([(2, 3)], tree.candidates)

        tree.update_words(2, ['charlie'])
        self.assertEqual([], tree.candidates)

class TreeGetWordsTestSuite(unittest.TestCase):
    """Tree.get_words() test cases."""

    def test_returns_word_when_single_word_records(self):
        tree = Tree(1)
        tree.build(['alpha', 'blue', 'charlie', 'delta'])

        tree.mergeCandidates([(0, 1)], 0)
        self.assertEqual([(0, 1)], tree.candidates)
        self.assertEqual([['alpha']], tree.get_words(0))

    def test_returns_words_from_avaialble_candidates(self):
        tree = Tree(1)
        tree.build(['alpha', 'bids', 'blue', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        tree.mergeCandidates([(0, 2)], 0)
        self.assertEqual([(0, 2)], tree.candidates)
        self.assertEqual([['alpha'], ['bids']], tree.get_words(0))

        tree.mergeCandidates([(0, 3)], 0)
        self.assertEqual([(0, 3)], tree.candidates)
        self.assertEqual([['alpha'], ['bids'], ['blue']], tree.get_words(0))

        tree.mergeCandidates([(0, 4)], 0)
        self.assertEqual([(0, 4)], tree.candidates)
        self.assertEqual([['alpha'], ['bids'], ['blue'], ['carves']], tree.get_words(0))

        tree.mergeCandidates([(1, 4)], 0)
        self.assertEqual([(1, 4)], tree.candidates)
        self.assertEqual([['bids'], ['blue'], ['carves']], tree.get_words(0))

        tree.mergeCandidates([(2, 4)], 0)
        self.assertEqual([(2, 4)], tree.candidates)
        self.assertEqual([['blue'], ['carves']], tree.get_words(0))

        tree.mergeCandidates([(3, 4)], 0)
        self.assertEqual([(3, 4)], tree.candidates)
        self.assertEqual([['carves']], tree.get_words(0))

    def test_returns_word_when_multiple_words_records_scanWindow_2(self):
        tree = Tree(2)
        tree.build(['alpha', 'bids', 'blue', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        tree.mergeCandidates([(0, 2)], 0)
        self.assertEqual([(0, 2)], tree.candidates)
        self.assertEqual([['alpha', 'bids'], ['bids', 'blue']], tree.get_words(1))

        tree.mergeCandidates([(0, 3)], 0)
        self.assertEqual([(0, 3)], tree.candidates)
        self.assertEqual([['alpha', 'bids'], ['bids', 'blue'], ['blue', 'carves']], tree.get_words(1))

        tree.mergeCandidates([(0, 4)], 0)
        self.assertEqual([(0, 4)], tree.candidates)
        self.assertEqual([['alpha', 'bids'], ['bids', 'blue'], ['blue', 'carves'], ['carves', 'charlie']], tree.get_words(1))

        tree.mergeCandidates([(1, 4)], 0)
        self.assertEqual([(1, 4)], tree.candidates)
        self.assertEqual([['bids', 'blue'], ['blue', 'carves'], ['carves', 'charlie']], tree.get_words(1))

        tree.mergeCandidates([(2, 4)], 0)
        self.assertEqual([(2, 4)], tree.candidates)
        self.assertEqual([['blue', 'carves'], ['carves', 'charlie']], tree.get_words(1))

        tree.mergeCandidates([(3, 4)], 0)
        self.assertEqual([(3, 4)], tree.candidates)
        self.assertEqual([['carves', 'charlie']], tree.get_words(1))

    def test_returns_word_when_multiple_words_records_scanWindow_3(self):
        tree = Tree(3)
        tree.build(['alpha', 'bids', 'blue', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        tree.mergeCandidates([(0, 2)], 0)
        self.assertEqual([(0, 2)], tree.candidates)
        self.assertEqual([['alpha', 'bids', 'blue'], ['bids', 'blue', 'carves']], tree.get_words(2))

        tree.mergeCandidates([(0, 3)], 0)
        self.assertEqual([(0, 3)], tree.candidates)
        self.assertEqual([['alpha', 'bids', 'blue'], ['bids', 'blue', 'carves'], ['blue', 'carves', 'charlie']], tree.get_words(2))

        tree.mergeCandidates([(0, 4)], 0)
        self.assertEqual([(0, 4)], tree.candidates)
        self.assertEqual([['alpha', 'bids', 'blue'], ['bids', 'blue', 'carves'], ['blue', 'carves', 'charlie'], ['carves', 'charlie', 'dances']], tree.get_words(2))

        tree.mergeCandidates([(1, 4)], 0)
        self.assertEqual([(1, 4)], tree.candidates)
        self.assertEqual([['bids', 'blue', 'carves'], ['blue', 'carves', 'charlie'], ['carves', 'charlie', 'dances']], tree.get_words(2))

        tree.mergeCandidates([(2, 4)], 0)
        self.assertEqual([(2, 4)], tree.candidates)
        self.assertEqual([['blue', 'carves', 'charlie'], ['carves', 'charlie', 'dances']], tree.get_words(2))

        tree.mergeCandidates([(3, 4)], 0)
        self.assertEqual([(3, 4)], tree.candidates)
        self.assertEqual([['carves', 'charlie', 'dances']], tree.get_words(2))

    def test_ignores_punctuation_at_the_end_of_a_word(self):
        tree = Tree(1)
        tree.build(['alpha.', 'bids,', 'blue,', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        tree.mergeCandidates([(0, 3)], 0)
        self.assertEqual([(0, 3)], tree.candidates)
        self.assertEqual([['alpha'], ['bids'], ['blue']], tree.get_words(0))

class TreeIsContainTestSuite(unittest.TestCase):
    """Tree.is_contain() test cases."""

    def test_scanWindow_1(self):
        tree = Tree(1)
        tree.build(['alpha.', 'bids,', 'blue,', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        self.assertEqual(True, tree.is_contain('alpha'))
        self.assertEqual(True, tree.is_contain('alpha.'))
        self.assertEqual(True, tree.is_contain('bids'))
        self.assertEqual(True, tree.is_contain('blue'))

        self.assertEqual(False, tree.is_contain('bids.'))
        self.assertEqual(False, tree.is_contain('back'))

    def test_scanWindow_2(self):
        tree = Tree(2)
        tree.build(['alpha.', 'bids,', 'blue', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        self.assertEqual(True, tree.is_contain('alpha. bids'))
        self.assertEqual(True, tree.is_contain('alpha. bids,'))
        self.assertEqual(True, tree.is_contain('bids'))
        self.assertEqual(True, tree.is_contain('bids, blue'))
        self.assertEqual(True, tree.is_contain('blue'))
        self.assertEqual(True, tree.is_contain('blue carves'))

        self.assertEqual(False, tree.is_contain('bids blue'))
        self.assertEqual(False, tree.is_contain('bids charlie'))

class TreeCalcFrequencyTestSuite(unittest.TestCase):
    """Tree.calc_frequency() test cases."""

    def test_scanWindow_1_non_repeated(self):
        tree = Tree(1)
        tree.build(['alpha.', 'bids,', 'blue,', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        self.assertEqual(1, tree.calc_frequency('alpha'))
        self.assertEqual(1, tree.calc_frequency('alpha.'))
        self.assertEqual(1, tree.calc_frequency('bids'))
        self.assertEqual(1, tree.calc_frequency('blue'))

        self.assertEqual(0, tree.calc_frequency('bids.'))
        self.assertEqual(0, tree.calc_frequency('back'))

    def test_scanWindow_2_non_repeated(self):
        tree = Tree(2)
        tree.build(['alpha.', 'bids,', 'blue,', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        self.assertEqual(1, tree.calc_frequency('alpha. bids'))
        self.assertEqual(1, tree.calc_frequency('alpha. bids,'))
        self.assertEqual(1, tree.calc_frequency('bids'))
        self.assertEqual(1, tree.calc_frequency('bids, blue'))
        self.assertEqual(1, tree.calc_frequency('blue'))

        self.assertEqual(0, tree.calc_frequency('blue carves'))
        self.assertEqual(0, tree.calc_frequency('bids blue'))
        self.assertEqual(0, tree.calc_frequency('bids charlie'))

    def test_scanWindow_1_repeated(self):
        tree = Tree(1)
        tree.build(['alpha.', 'alpha', 'alpha,', 'bids,', 'blue,', 'carves', 'charlie', 'dances', 'delta', 'eats', 'blue', 'blue'])

        self.assertEqual(3, tree.calc_frequency('alpha'))
        self.assertEqual(1, tree.calc_frequency('alpha.'))
        self.assertEqual(1, tree.calc_frequency('bids'))
        self.assertEqual(3, tree.calc_frequency('blue'))

        self.assertEqual(0, tree.calc_frequency('bids.'))
        self.assertEqual(0, tree.calc_frequency('back'))

    def test_scanWindow_2_repeated(self):
        tree = Tree(2)
        tree.build(['alpha.', 'alpha', 'alpha,', 'bids,', 'blue,', 'carves', 'charlie', 'dances', 'delta', 'eats', 'blue', 'blue'])

        self.assertEqual(3, tree.calc_frequency('alpha'))
        self.assertEqual(3, tree.calc_frequency('blue'))

        self.assertEqual(1, tree.calc_frequency('alpha,'))
        self.assertEqual(1, tree.calc_frequency('bids'))
        self.assertEqual(1, tree.calc_frequency('bids, blue'))

        self.assertEqual(0, tree.calc_frequency('alpha. bids,'))
        self.assertEqual(0, tree.calc_frequency('alpha. bids'))
        self.assertEqual(0, tree.calc_frequency('blue carves'))
        self.assertEqual(0, tree.calc_frequency('bids blue'))
        self.assertEqual(0, tree.calc_frequency('bids charlie'))

class TreeCalcMostFrequentNextWordTestSuite(unittest.TestCase):
    """Tree.calc_most_frequent_next_word() test cases."""

    def test_scanWindow_1_non_repeated_negative(self):
        tree = Tree(1)
        tree.build(['alpha.', 'bids,', 'blue,', 'carves', 'charlie', 'dances', 'delta', 'eats'])

        self.assertEqual(('', 0), tree.calc_most_frequent_next_word('alpha'))
        self.assertEqual(('', 0), tree.calc_most_frequent_next_word('alpha.'))
        self.assertEqual(('', 0), tree.calc_most_frequent_next_word('back'))
        self.assertEqual(('', 0), tree.calc_most_frequent_next_word('something'))

    def test_scanWindow_2_repeated_negative(self):
        tree = Tree(2)
        tree.build(['down', 'the', 'street', 'down', 'the', 'path', 'down', 'the', 'well'])

        self.assertEqual(('', 0), tree.calc_most_frequent_next_word('down the'))

    def test_scanWindow_2_repeated_positive(self):
        tree = Tree(2)
        tree.build(['down', 'the', 'street', 'down', 'the', 'path', 'down', 'the', 'well'])

        self.assertEqual(('the', 3), tree.calc_most_frequent_next_word('down'))
        self.assertEqual(('path', 1), tree.calc_most_frequent_next_word('the'))

    def test_scanWindow_3_repeated_positive(self):
        tree = Tree(3)
        tree.build(['down', 'the', 'street', 'down', 'the', 'path', 'down', 'the', 'well'])

        self.assertEqual(('the', 3), tree.calc_most_frequent_next_word('down'))
        self.assertEqual(('path', 1), tree.calc_most_frequent_next_word('down the'))
        self.assertEqual(('path', 1), tree.calc_most_frequent_next_word('the'))

if __name__ == 'main':
    unittest.main()