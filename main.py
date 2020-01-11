from text_generator.Tree import Tree
from text_generator.TextGenerator import TextGenerator

if __name__ == "__main__":
    tree = Tree(3)
    tree.build('hello wor*ld how are you how are How do yo-u do ')

    # print(tree.is_contain("hello wOr*ld how "))   # True
    # print(tree.is_contain("how do yo-u do "))     # True
    # print(tree.is_contain("wor*LD how a"))     # True
    
    # print(tree.find_nextword("how do yo-u "))     # do
    # print(tree.find_nextword("how do your "))    # None
    # print(tree.find_nextword("how are "))      # you or how
    # print(tree.find_nextword("how are "))      # you or how

    import smart_open
    import pickle

    #entailData = sys.argv[1]        # entailData to make tree
    entailData = "data/1661-0.txt"

    #tree = Tree(4, 3, "SplitedWindows")
    tree = Tree(4)
    words = []
    with smart_open.open(entailData, 'r', encoding='utf-8') as entail:
        for line in entail:
            words.extend(line.strip().split())

    tree.build(words)
    print(tree.records)

    print("Saving Tree to \"Tree\"")
    with open("Tree", 'wb') as outfile:
        pickle.dump(tree, outfile)

    print("Saving Tree done")

    tree.update_words(0, ["today", "Are", "Earth", "hit", "a"])
    tree.update_words(1, ["meteor,", "Earth,"])
    print(tree.get_words(2))

    print(tree.is_contain("meteor, "))
    print(tree.is_contain("a "))
    print(tree.is_contain("a, "))

    print(tree.calc_frequency("meteor, "))
    print(tree.calc_frequency("a "))
    print(tree.calc_frequency("a, "))    
    print("yes yes yes yes", tree.calc_frequency("yes yes yes yes"))

if __name__ == "__main__":
    entailData = "data/entailData.txt"  # entailData to make tree
    gloveModel = "data/glove_model.txt"        # glove model which is converted with glove2word2vector.py
    commonWordFile = "data/wiki-100k.txt"    # wiki common word file.

    textgenerator = TextGenerator(window=7, verify=2, ofTranslates=140, ofMatches=150, ofOriginalsNearNextWord=2, CommasPerSentence=1, WordsPerCommaOrPeriod=(3,3),
                                  commonWordCoefficient=(0.0001, 60, 0.001), contextualCoefficient=(1, 1, 2.3))
                               # window, verify, ofTranslates, ofMatches, ofOriginalsNearNextWord, CommasPerSentence, WordsPerCommaOrPeriod, commonWordCoefficient, contextualCoefficient
    textgenerator.load_CommonWord(commonWordFile)
    # textgenerator.init_Tree(entailData)
    textgenerator.load_Tree()
    textgenerator.load_Model(gloveModel)

    while True:    # infinite loop
        seed = input("\nPlease input seed text here:\n")
        if seed == "":
          break
        textgenerator.morph_seed(seed, 15)