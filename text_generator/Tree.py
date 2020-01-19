from .functions import *
import operator

class Tree(object):
    """
    Our tree implementation.
    """

    def __init__(self, scanWindowSz, debug=False):
        self.scanWindowSz = scanWindowSz
        self.lenRecords = 0                 # number of records
        self.records = []                   # all hypo records made from entailData for fast search of scanWindow or verification
        self.candidates = []
        self.debug = debug

    def build(self, text:list):
        if self.debug:
            print("Building Tree...")

        length = len(text)
        self.records = []

        for i in range(0, length):
            windowSize= min(self.scanWindowSz, length - i)
            shouldInsert = True
            for word in text[i:i+windowSize]:
                if word.isalpha():
                    continue

                all_but_last = word[:-1]
                if not all_but_last.isalpha():
                    shouldInsert = False
                    break

                last = word[-1]
                if not (last.isalpha() or last in ['.', ',', '!', '?']):
                    shouldInsert = False
                    break

            if shouldInsert:
                lower_words = [w.lower() for w in text[i:i+windowSize]]
                self.records.append(' '.join(lower_words))

        self.records.sort()
        self.lenRecords = len(self.records)

        if self.debug:
            print(self.records)
            print("Building Tree done.")

    def find_interval(self, searchStr, lo=0, hi=None):
        if (hi == None):
            hi = self.lenRecords
        fro = lower_bound(self.records, searchStr, lo, hi)
        to = upper_bound(self.records, searchStr, lo, hi)
        return fro, to

    def mergeCandidates(self, candidates, word_cluster_size):
        """Merges candidates.
        word_cluster_size -- number. How many words to consider in each record before we consider them
          to be the in a single cluster of candidates.
        candidates -- list(tuple). Each tuple is a (start_idx, end_idx) of candidate words.
          As such, it is assumed that start_idx <= end_idx.
        """
        # print("before", self.candidates)
        self.candidates = []
        if (len(candidates) == 0):
            return

        def isSameCluster(a, b, max_index):
            a = a.split()
            b = b.split()
            # if any of the records has less words than max_index + 1, they're not the same cluster
            if len(a) < max_index + 1 or len(b) < max_index + 1:
                return False

            # if any of the words in candidate a is different than the candidate b (up to max_index words),
            # they're not the same cluster
            for i in range (0, max_index + 1):
                if a[i] != b[i]:
                    return False
            return True

        candidates.sort(key = operator.itemgetter(0, 1))
        #print(f'candidates: {candidates}')
        self.candidates.append(candidates[0])
        for candy in candidates:
            (last_candidate_start_idx, last_candidate_end_idx) = self.candidates[-1]
            # if the current candidate.start_idx > last candidate.end_idx, this tuple must be higher in general.
            if candy[0] > last_candidate_end_idx:
                self.candidates.append(candy)
            else: # if current candidate.start_idx <= last_candidate.end_idx
                # if the records are the same comparing up to word_cluster_size words
                if isSameCluster(self.records[last_candidate_start_idx], self.records[candy[0]], word_cluster_size):
                    # merge the last candidate and the current one by picking the biggest end_idx
                    self.candidates[-1] = (last_candidate_start_idx, max(last_candidate_end_idx, candy[1]))
                else:
                    # otherwise, add the range as a new candidate
                    self.candidates.append(candy)

    def update_words(self, word_position:int, word_list:list):
        """Updates the set of available candidates by searching words that expand the current set of candidates.

        word_position: indicates the position in the record for which words will be compared.
          If 0, all records are considered in the search.
          If not 0, only (lo, hi) combinations from self.candidates are used in the search.

        word_list: the words to evaluate.
        """

        if word_position == 0:
            candidates = []
            for searchStr in word_list:
                fro, to = self.find_interval(searchStr + " ")
                if fro < to:
                    candidates.append((fro, to))
        else:
            candidates = []
            for (fro, to) in self.candidates:
                for word in word_list:
                    searchStr = ' '.join(self.records[fro].split()[:word_position]) + " " + word + " "
                    froNew, toNew = self.find_interval(searchStr, fro, to)
                    if froNew < toNew:
                        candidates.append((froNew, toNew))

        # print(candidates)
        self.mergeCandidates(candidates, word_position)
        # print(self.candidates)

    def get_words(self, idx:int):
        """
        return word list of vanila serarch ex. [[down the street], [up the street], [down the stair], ...]
        here predicted next word is [street, stair, ...]
        """

        resultSet = []
        for (fro, to) in self.candidates:
            for sequence in self.records[fro:to]:
                word_list = sequence.split()
                if (len(word_list) > idx):
                    resultSet.append(' '.join(word_list[:idx+1]))

        result = []
        for hp in resultSet:
            words = hp.split()
            if words[-1][-1]==',' or words[-1][-1]=='.':
                words[-1] = words[-1][:-1]
            if words[-1] == "":
                continue
            result.append(words)

        return result

    def is_contain(self, searchStr:str) -> bool:
        """
        check if a tree contain searchStr
        """
        fro, to = self.find_interval(searchStr)
        if fro < to:
            return True
        else:
            return False

    def calc_frequency(self, searchStr:str) -> int:
        """
        calculate the number of occurances of search str in entailData
        """
        fro, to = self.find_interval(searchStr)
        if fro < to:
            return to-fro
        else:
            return 0

    def calc_most_frequent_next_word(self, searchStr:str):
        """
        calcuate the most frequent next word of a SearchStr ex. "down the " -> "path, 15"
        """
        L = len(searchStr.strip().split())
        fro, to = self.find_interval(searchStr)

        cur_word = ""
        cur_cnt = 0
        max_cnt = 0
        max_word = ""
        for sequence in self.records[fro:to]:
            word_list = sequence.split()
            if (len(word_list) <= L):
                continue

            word = word_list[L]
            if word == cur_word:
                cur_cnt += 1
            else:
                if cur_cnt > max_cnt:
                    max_cnt = cur_cnt
                    max_word = cur_word

                cur_word = word
                cur_cnt = 1
        
        if cur_cnt > max_cnt:
            max_cnt = cur_cnt
            max_word = cur_word

        return (max_word, max_cnt)

    def print(self):
        print(f'Scan window size: {self.scanWindowSz}')
        print(f'Number of records: {self.lenRecords}')
        print(f'Records: {self.records}')
        print(f'Candidates: {self.candidates}')
