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

if __name__ == 'main':
    unittest.main()