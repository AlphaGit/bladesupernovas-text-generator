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

if __name__ == 'main':
    unittest.main()