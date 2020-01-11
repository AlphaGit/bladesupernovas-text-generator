from .functions import *
import operator

class Tree(object):
    """
    Our tree implementation.
    """

    def __init__(self, scanWindowSz):
        self.scanWindowSz = scanWindowSz
        self.lenRecords = 0                 # number of records
        self.records = []                   # all hypo records made from entailData for fast search of scanWindow or verification
        self.candidates = []

    def build(self, text:list):
        print("Building Tree...")

        def make_record(word_list):
            res = ""
            for word in word_list:
                res += word.lower() + " "
            return res.strip()

        length = len(text)
        self.records = []

        for i in range(0, length):
            windowSize= min(self.scanWindowSz, length - i)
            shouldInsert = True
            for word in text[i:i+windowSize]:
                if not(word.isalpha() or (word[:-1].isalpha() and (word[-1]==',' or word[-1]=='.'))):
                    shouldInsert = False
                    break
            if shouldInsert == True:
                self.records.append(make_record(text[i:i+windowSize]))

        self.records.sort()
        self.lenRecords = len(self.records)

        # print(self.records)
        # print("Building Tree done")

    def find_interval(self, searchStr, lo=0, hi=None):
        if (hi == None):
            hi = self.lenRecords
        fro = lower_bound(self.records, searchStr, lo, hi)
        to = upper_bound(self.records, searchStr, lo, hi)
        return fro, to

    def mergeCandidates(self, candidates, idx):
        # print("before", self.candidates)
        self.candidates = []
        if (len(candidates) == 0):
            return

        def isSameCluster(a, b, verifyLen):
            a = a.split()
            b = b.split()
            if len(a) < verifyLen + 1 or len(b) < verifyLen + 1:
                return False
            
            for i in range (0, verifyLen+1):
                if a[i] != b[i]:
                    return False
            return True


        candidates.sort(key = operator.itemgetter(0, 1))
        self.candidates.append(candidates[0])
        for candy in candidates:
            if candy[0] > self.candidates[-1][1]:
                self.candidates.append(candy)
            else:
                if isSameCluster(self.records[self.candidates[-1][0]], self.records[candy[0]], idx):
                    self.candidates[-1] = (self.candidates[-1][0], max(self.candidates[-1][1], candy[1]))
                else:
                    self.candidates.append(candy)


    def update_words(self, idx:int, word_list:list):
        # print(idx, word_list)
        if idx == 0:
            candidates = []
            for searchStr in word_list:
                fro, to = self.find_interval(searchStr + " ")
                if fro < to:
                    candidates.append((fro, to))
        else:
            candidates = []
            for (fro, to) in self.candidates:
                for word in word_list:
                    searchStr = ' '.join(self.records[fro].split()[:idx]) + " " + word + " "
                    froNew, toNew = self.find_interval(searchStr, fro, to)
                    if froNew < toNew:
                        candidates.append((froNew, toNew))

        # print(candidates)
        self.mergeCandidates(candidates, idx)
        # print(self.candidates)

    def dist(self, a, b):
        L = min(len(a), len(b))
        nSame = 0
        pattern = 0
        for i in range(0, L):
            if a[i] == b[i]:
                nSame = nSame + 1
                pattern = pattern + (1<<i)
        
        return (nSame, pattern)

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