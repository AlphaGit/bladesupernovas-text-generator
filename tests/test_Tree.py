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

if __name__ == 'main':
    unittest.main()