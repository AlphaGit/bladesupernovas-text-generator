from __future__ import division
import sys
import gensim
import smart_open
import numpy
import random
#from Tree import Tree
import pickle
import heapq
import math
#import keyboard

DEBUG = False

class TextGenerator(object):
    def __init__(self, window=4, verify=2, ofTranslates=2, ofMatches=1, ofOriginalsNearNextWord=0, CommasPerSentence=2, WordsPerCommaOrPeriod=(4,7),
                     commonWordCoefficient=(1, 100, 0.0011), contextualCoefficient=(1, 0.000001, 0.0002)):
        self.Tree = None
        self.w2vModel = None
        self.window = window
        self.verify = verify
        self.ofMatches = ofMatches
        self.ofTranslates = ofTranslates
        self.ofOriginalsNearNextWord = ofOriginalsNearNextWord
        self.CommasPerSentence = CommasPerSentence
        self.WordsPerCommaOrPeriod = WordsPerCommaOrPeriod
        self.commonWordCoefficient = commonWordCoefficient
        self.contextualCoefficient = contextualCoefficient
        self.TreeSaveName = "Tree"
        self.treeScanwindow = max(window + 1, verify)
        self.translatesBucket = {}                           # translatesbucket to contain all translates of words up to now.
        self.pickfromTranslatesBucket = 1                   # how many words we should pick from a bucket for softmax.
        self.addToTranslatesBucket = 30                      # how many gloves of a word we should insert to translatesBucket.
        self.nofFrequencyCheckCandidates = 8                 # how many last candidates we should check for frequency.
        self.lenFrequencyCheckWindow = 2                     # length of frequency check window.
        self.fakeCommaChoiceBucket = []
        self.seed_word_list = []
        self.wordTransScore = {}


    def load_Model(self, model_file):
        print("Loading w2v model from \"{}\"...".format(model_file))
        self.w2vModel = gensim.models.KeyedVectors.load_word2vec_format(model_file, binary=False)  # GloVe Model
        print("Loading w2v model done")

    def save_Tree(self):
        print("Saving Tree to \"{}\"".format(self.TreeSaveName))
        with open(self.TreeSaveName, 'wb') as outfile:
            pickle.dump(self.Tree, outfile)
        print("Saving Tree done")

    def load_Tree(self):
        print("Loading Tree from \"{}\"...".format(self.TreeSaveName))
        with open(self.TreeSaveName, 'rb') as infile:
            self.Tree = pickle.load(infile)
        print("Loading Tree done")

    def init_Tree(self, entailData: str):
        """
        Function to construct tree from entailData
        """
        self.Tree = Tree(self.treeScanwindow)
        words = []
        with smart_open.smart_open(entailData, 'r') as entail:
            for line in entail:
                words.extend(line.strip().split())

        self.Tree.build(words)
        self.save_Tree()
        # if DEBUG:
             # print(self.Tree.records)

    def load_CommonWord(self, wordFile: str):
        self.wordTransScore = {}
        cnt = 1
        with smart_open.smart_open(wordFile, encoding='utf8') as f:
            for line in f:
                splited_line = line.strip().split()
                word = splited_line[0].lower()
                if len(splited_line) == 1 and word[0] != '#':
                    if not word in self.wordTransScore:
                        self.wordTransScore[word] = cnt
                        cnt = cnt + 1
        
        """
        we are using following function for exponential curve according to word list.
        y = k * exp(-a * x) + b
        this curve will pass 2 points (1, M1) & (L, M2)
        a will be the incline prameter.
        """

        M1 = self.commonWordCoefficient[1]
        M2 = self.commonWordCoefficient[0]
        a = self.commonWordCoefficient[2]
        L = len(self.wordTransScore)

        k = (M1 - M2) / (math.exp(-a) - math.exp(-a*L))
        b = (M2 * math.exp(-a) - M1 * math.exp(-a*L)) / (math.exp(-a) - math.exp(-a*L))
        

        for word in self.wordTransScore:
            self.wordTransScore[word] = M1 + M2 -(k * math.exp(-a*(self.wordTransScore[word])) + b)
            # if DEBUG:
            # print(word, self.wordTransScore[word])

    def calc_Transscore(self, word:str):
        if word in self.wordTransScore:
            return self.wordTransScore[word]
        else:
            return self.commonWordCoefficient[1]

    def makeGlove(self, word, ofTranslates):
        if word[-1] == "," or word[-1] == ".":
            suffix = word[-1]
            word = word[:-1]
        else:
            suffix = ''
        word_list = [word + suffix]
        try:
            for tup in self.w2vModel.similar_by_word(word, ofTranslates):
                word_list.append(tup[0] + suffix)
        except:
            pass
        return word_list

    def insertToTranslatesBucket(self, insert_word, seed_word):
        insert_score = self.calc_Transscore(seed_word)
        if insert_word in self.translatesBucket:
            self.translatesBucket[insert_word] += insert_score
        else:
            self.translatesBucket[insert_word] = insert_score

    def pickNextword(self, hypolist):                   #
        predictedHypoList = []
        IndexesofPredictedHypo = {}

        for idx, hp in enumerate(hypolist):
            word, cnt = hp[0][-1], hp[1]
            if not (word in predictedHypoList):
                predictedHypoList.append(word)
                IndexesofPredictedHypo[word] = [idx]
            else:
                IndexesofPredictedHypo[word].append(idx)

        def dist(hp, orig):
            L = len(hp) - 1
            ret = 0
            for i in range(0, L):
                if hp[-2-i] == orig[-1-i]:
                    ret += 1
            return ret

        if DEBUG:
            print("Scores of each word")
            print("{:<20}: {:<10}: {:<10}, {:<10}, {:<10}, {:<10}".format("word", "score", "TransScore", "LenScore", "Contextual", "Originals"))
        
        relatedTranslatesBucket = []

        M1 = self.contextualCoefficient[1]
        M2 = self.contextualCoefficient[0]
        a = self.contextualCoefficient[2]
        L = self.window + 1

        k = (M2 - M1) / (math.exp(L*a) - math.exp(a))
        b = (M1 * math.exp(L*a) - M2 * math.exp(a)) / (math.exp(L*a) - math.exp(a))

        for word in predictedHypoList:
            maxLen = 0
            contextualFrequency = 0
            originals = 0
            for idx in IndexesofPredictedHypo[word]:
                curLen = len(hypolist[idx][0])
                maxLen = max(maxLen, curLen)
                exponentialCoeff = (k * math.exp(a*curLen) + b) * hypolist[idx][1]
                contextualFrequency += exponentialCoeff
                originals += exponentialCoeff * dist(hypolist[idx][0], self.seed_word_list)

            if word in self.translatesBucket:
                transScore = self.translatesBucket[word]
            else:
                transScore = 0

            score = transScore + maxLen + contextualFrequency + originals
            if DEBUG:
                print("{:<20}: {:10.4f}: {:10.4f}, {:10.4f}, {:10.4f}, {:10.4f}".format(word, score, transScore, maxLen, contextualFrequency, originals))

            relatedTranslatesBucket.append((score, word))

        ntopCandidates = min(self.pickfromTranslatesBucket, len(predictedHypoList))
        topCandidates = heapq.nlargest(ntopCandidates, relatedTranslatesBucket)

        predictedHypoList = []
        softMaxVals = []

        for (score, word) in topCandidates:
            softMaxVals.append(score)
            predictedHypoList.append(word)

        return random.choices(predictedHypoList, weights=softMaxVals)[0]

    def predict(self, input_seed: list) -> str:
        """
        Function to predict next word of a sentence.
        """

        self.seed_word_list = []
        for word in input_seed:
            self.seed_word_list.append(word.lower())

        verified_hypo_list = []
        total_verified = 0
        windowLen = min(len(input_seed), self.window)

        while windowLen > 0:
            ofOriginalsNearNextWord = min(windowLen, self.ofOriginalsNearNextWord)
            verifyLen = min(self.verify, windowLen + 1)

            ## get window list from seed word list
            windowlist = self.seed_word_list[-windowLen:]

            ## make listoflists
            listoflists = []

            idx = -1
            for i, word in enumerate(windowlist):
                if word[-1] == ',' or word[-1] == '.':
                    idx = i

            for i, word in enumerate(windowlist):
                if i == idx:
                    listoflists.append(self.makeGlove(word, self.ofTranslates))
                else:
                    listoflists.append(self.makeGlove(self.stem_Word(word), self.ofTranslates))

            if DEBUG:
                print("Lists of %d word window =" % windowLen, listoflists)

            ## do vanilla search
            idx = 0
            for word_list in listoflists:
                self.Tree.update_words(idx, word_list)
                idx = idx + 1
            
            ## get all hypothesis of next word
            hypo_list = self.Tree.get_words(idx)

            if DEBUG:
                print("hypo_list = ", hypo_list)

            def is_ofOriginalsNearNextWord(a, b, L):
                """
                check if last L words of a[:-1] are same as b[-L:]
                """
                for i in range(L):
                    if a[-i-2] != b[-i-1]:
                        return False
                return True

            ## get ofOriginalNearNextWord list
            ofOs_hypo_list = []
            for hp in hypo_list:
                if is_ofOriginalsNearNextWord(hp, windowlist, ofOriginalsNearNextWord) == True:
                    ofOs_hypo_list.append(hp)
            if DEBUG:
                print("ofOs_hypo_list = ", ofOs_hypo_list)

            def add_to_verified_HypoList(hp):
                kLen = 0            # sum of length that contain this hp in verified hypo list.
                jdx = -1            # index fo current hp in verified hypo list.
                lenVerified = len(verified_hypo_list)
                for idx in range(0, lenVerified):
                    prev = verified_hypo_list[idx][0]
                    L = len(hp)
                    isContained = True
                    for i in range(L):
                        if hp[-i-1] != prev[-i-1]:
                            isContained = False
                            break
                    if isContained == True:
                        if len(prev) == L:
                            jdx = idx
                        else:
                            kLen += verified_hypo_list[idx][1]

                ret = 1

                if jdx == -1:
                    if kLen == 0:
                        verified_hypo_list.append((hp, 1))
                    else:
                        verified_hypo_list.append((hp, 1-kLen))
                        ret -= kLen

                else:
                    verified_hypo_list[jdx] = (verified_hypo_list[jdx][0], verified_hypo_list[jdx][1]+1)

                return ret

            ## do verification
            prefix = ' '.join(windowlist[-verifyLen+1:])
            for hp in ofOs_hypo_list:
                search_str = prefix + " " + hp[-1] + " "
                search_str_comma = prefix + " " + hp[-1] + ", "
                search_str_stop = prefix + " " + hp[-1] + ". "
                if self.Tree.is_contain(search_str) == True or self.Tree.is_contain(search_str_comma) == True or self.Tree.is_contain(search_str_stop) == True:        # verified
                    total_verified += add_to_verified_HypoList(hp)

            if DEBUG:
                print("verified_hypo_list = ", verified_hypo_list)

            if total_verified >= self.ofMatches:
                break
            else:
                windowLen = windowLen - 1
        
        if total_verified == 0:
            print("Matches =", [])
            return None

        def dist(hp, orig):
            L = len(hp) - 1
            LO = len(orig)
            nSame = 0
            pattern = 0
            for i in range(0, L):
                if hp[-2-i] == orig[-1-i]:
                    nSame = nSame + 1
                    pattern = pattern + (1<<(LO-i))
            
            return (nSame, pattern)

        windowlist = self.seed_word_list[-self.window:]

        L = len(verified_hypo_list)

        ofMatches = min(total_verified, self.ofMatches)

        for i in range(0, L):
            for j in range(i+1, L):
                if dist(verified_hypo_list[i][0], windowlist) < dist(verified_hypo_list[j][0], windowlist):
                    verified_hypo_list[i], verified_hypo_list[j] = verified_hypo_list[j], verified_hypo_list[i]

        curMatches = 0
        for i in range(0, L):
            curMatches += verified_hypo_list[i][1]
            if curMatches >= ofMatches:
                verified_hypo_list[i] = (verified_hypo_list[i][0], verified_hypo_list[i][1]-(curMatches-ofMatches))
                verified_hypo_list = verified_hypo_list[:i+1]
                break

        matcheStr = []
        for hp in verified_hypo_list:
            matcheStr.append((' '.join(hp[0]), hp[1]))

        print("Matches =", matcheStr)
        return self.pickNextword(verified_hypo_list)

    def calcCommaLen(self, words):
        L = len(words)
        for i in range(L):
            if words[-i-1][-1] == '.' or words[-i-1][-1] == ',':
                return i
        return L
    
    def stem_Word(self, word):
        res = word.lower()
        if res[-1] == '.' or res[-1] == ',':
            res = res[:-1]
        return res

    def make_FirstWord(self, word):
        res = word[0].upper() + word[1:]
        return res
    
    def isLastCandidateMostFrequent(self, words):
        """
        check if the last candidates is most frequent in entailData if we add comma/stop.
        """
        if DEBUG:
            print("Checking if last word is most frequent for hypo -> ", ' '.join(words))

        L = len(words)
        last_frequency = 0
        most_frequency = 0
        for i in range(self.nofFrequencyCheckCandidates):
            if L-self.lenFrequencyCheckWindow-i<0:
                break
            candy = []
            for j in range(self.lenFrequencyCheckWindow):
                candy.append(self.stem_Word(words[L-self.lenFrequencyCheckWindow-i+j]))
            
            comma_cnt = self.Tree.calc_frequency(' '.join(candy)+', ')
            stop_cnt = self.Tree.calc_frequency(' '.join(candy)+'. ')
            total_cnt = self.Tree.calc_frequency(' '.join(candy) + ' ') + comma_cnt + stop_cnt
            # next_word, next_cnt = self.Tree.calc_most_frequent_next_word(' '.join(candy)+' ')

            # if next_cnt == 0:
            if total_cnt == 0:
                freq=0
            else:
                # freq = (comma_cnt + stop_cnt)/next_cnt
                freq = (comma_cnt + stop_cnt)/total_cnt

            if DEBUG:
                # print("\"{}\": {},\t\"{}\": {},\tMost freq next word: ({}, {}),\tFreq: {}".format(' '.join(candy)+",", comma_cnt, ' '.join(candy)+".", stop_cnt, next_word, next_cnt, freq))
                print("\"{}\": {},\t\"{}\": {},\tTotal : {},\tFreq: {}".format(' '.join(candy)+",", comma_cnt, ' '.join(candy)+".", stop_cnt, total_cnt, freq))

            if i == 0:
                last_frequency = freq
            else:
                most_frequency = max(most_frequency, freq)

        if last_frequency > most_frequency:
            return True
        else:
            return False

    def addNextWord(self, words, next_word):
        if words[-1][-1] == '.':
            words.append(self.make_FirstWord(next_word))
        else:
            words.append(next_word)

        for glove_next_word in self.makeGlove(next_word, self.addToTranslatesBucket):
            self.insertToTranslatesBucket(glove_next_word, next_word)

        if self.isLastCandidateMostFrequent(words) == False:                     # we couldn't add any comma/stop
            if DEBUG:
                print("we can't add comma due to last word frequency rule.")
            return words

        commaLen = self.calcCommaLen(words)

        bshouldAddComma = False
        if commaLen >= self.WordsPerCommaOrPeriod[0]:
            if commaLen >= self.WordsPerCommaOrPeriod[1]:
                bshouldAddComma = True
            else:
                if random.choice([True, False]) == True:
                    bshouldAddComma = True
        
        L = len(words)

        if bshouldAddComma == True:                                                 # we should add real comma/stop
            numCommas = 0                                                        # calc number of commas in current sentence.
            for i in range(L):
                if words[-i-1][-1] == ',':
                    numCommas = numCommas + 1
                if words[-i-1][-1] == '.':
                    break
            
            """
            we have to add addCharacter(./,) after last word now.
            """
            if DEBUG:
                print("add real comma/stop")

            if numCommas >= self.CommasPerSentence:                             # we have to add stop
                words[-1] = words[-1] + '.'
            else:                                                               # we have to add comma
                words[-1] = words[-1] + ','
        else:
            if DEBUG:
                print("we can't add comma due to WordsPerCommaOrPeriod rule.")

        return words

    def morph_seed(self, seed: str, length):
        self.translatesBucket = {}
        words = seed.strip().split()

        for word in words:
            for glove_word in self.makeGlove(self.stem_Word(word), self.addToTranslatesBucket):
                self.insertToTranslatesBucket(glove_word, self.stem_Word(word))

        for i in range(length):
            print("Seed=" + " ".join(words))
            word = self.predict(words)
            if word == None:
                print("can't predict next word and end morphing.")
                return
            #if keyboard.is_pressed('q'):
            #    return
            words = self.addNextWord(words, word)
        print("Seed=" + " ".join(words))