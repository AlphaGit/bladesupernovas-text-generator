#include <chrono>
#include <iostream>
#include "OpenBLAS/cblas.h"
#include "Log.h"
#include "TextGenerator.h"

const char* COMMON_WORD_FILE = "wiki-100k.txt";
const char* ENTAIL_DATA = "entailData.txt";
const char* GLOVE_MODEL = "glove_model.txt"; //"glove.840B.300d.txt";
const int WORDS_TO_PREDICT = 200;

unsigned GloveTime, AllGloveTime, TreeTime, AllTreeTime;

TextGenerator::TextGenerator(const Params& params, Word2vec& model, Tree& tree, const char* commonWordsFilePath) :
	mW2vModel(model),
	mTree(tree),
	mRandomEngine(random_device{}()),
	mRandomBits(mRandomEngine)
{
	mWindow = params.window;
	mVerify = params.verify;
	mOfTranslates = params.ofTranslates;
	mOfMatches = params.ofMatches;
	mOfOriginalsNearNextWord = params.ofOriginalsNearNextWord;
	mCommasPerSentence = params.commasPerSentence;
	mWordsPerCommaOrPeriod = params.wordsPerCommaOrPeriod;
	mCommonWordCoefficient = params.commonWordCoefficient;
	mContextualCoefficient = params.contextualCoefficient;
	mPickFromTranslatesBucket = params.pickFromTranslatesBucket;
	mAddToTranslatesBucket = params.addToTranslatesBucket;
	mNofFrequencyCheckCandidates = params.nofFrequencyCheckCandidates;
	mLenFrequencyCheckWindow = params.lenFrequencyCheckWindow;

	if (!loadCommonWord(commonWordsFilePath))
		throw runtime_error("");
}

bool TextGenerator::loadCommonWord(const char* filePath)
{
	Log& log = Log::instance();
	log.print(0, "Loading common words from \"%s\"... ", filePath);
	ifstream file(filePath);
	if (!file) {
		log.print(0, "error\n");
		return false;
	}
	mWordTransScore.clear();
	string line;
	int count = 1;
	while (getline(file, line)) {
		char* s = (char*)line.data();
		for (; isspace((unsigned char)*s); ++s);
		const char* begin = s;
		if (*s == '#')
			continue;
		for (; *s && !isspace((unsigned char)*s); ++s)
			*s = (char)tolower((unsigned char)*s);
		const char* end = s;
		for (; isspace((unsigned char)*s); ++s);
		if (!*s && mWordTransScore.emplace(string(begin, end), count).second)
			++count;
	}
	--count;

	/*we are using following function for exponential curve according to word list.
		y = k * exp(-a * x) + b
		this curve will pass 2 points(1, M1) & (L, M2)
		a will be the incline prameter.*/
	double m1 = mCommonWordCoefficient[1];
	double m2 = mCommonWordCoefficient[0];
	ExpCurve expCurve(1, m1, count, m2, -mCommonWordCoefficient[2]);
	for (auto& word : mWordTransScore)
		word.second = m1 + m2 - expCurve(word.second);
	log.print(0, "done\n");
	return true;
}

void TextGenerator::morphSeed(const string& seed, int length)
{
	GloveTime = AllTreeTime = 0;
	Words words = split(seed);
	
	mTranslatesBucket.clear();
	for (const string& word : words) {
		string w = stemWord(word);
		Words glove = makeGlove(w, mAddToTranslatesBucket);
		for (const string& gloveWord : glove)
			insertToTranslatesBucket(gloveWord, w);
	}
	Log& log = Log::instance();
	log.print(0, "translates glove time: %g s\n", GloveTime / 1000.);

	auto start = chrono::steady_clock::now();
	AllGloveTime = GloveTime;
	int i;
	for (i = 0; i < length; i++) {
		GloveTime = TreeTime = 0;
		printWords(0, words, "Seed=");
		auto wordStart = chrono::steady_clock::now();
		string word = predict(words);
		if (!word.empty())
			addNextWord(words, word);
		std::chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - wordStart);
		log.print(0, "glove time: %g s\n", GloveTime / 1000.);
		log.print(0, "tree time: %g s\n", TreeTime / 1000.);
		log.print(0, "word time: %g s\n", duration.count() / 1000.);
		AllGloveTime += GloveTime;
		AllTreeTime += TreeTime;
		if (word.empty()) {
			log.print(0, "can't predict next word and end morphing.\n");
			break;
		}
	}
	std::chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - start);
	if (i == length)
		printWords(0, words, "Seed=");
	log.print(0, "total glove time: %g s\n", AllGloveTime / 1000.);
	log.print(0, "total tree time: %g s\n", AllTreeTime / 1000.);
	log.print(0, "total time: %g s\n", duration.count() / 1000.);
}

// Function to predict next word of a sentence.
string TextGenerator::predict(const Words& inputSeed)
{
	mSeedWordList = inputSeed;
	for (string& word : mSeedWordList)
		for (char& c : word)
			c = (char)tolower((unsigned char)c);

	vector<Hypo> verifiedHypoList;
	int totalVerified = 0;
	int windowLen = min((int)inputSeed.size(), mWindow);
	for (; windowLen > 0 && totalVerified < mOfMatches; windowLen--) {
		// get window list from seed word list
		Words windowList = getLastWords(mSeedWordList, windowLen);

		// make listoflists
		int commaPos = windowLen;
		while (--commaPos >= 0 && !isCommaOrStop(windowList[commaPos]));
		vector<Words> listOfLists;
		int i;
		for (i = 0; i < windowLen - mOfOriginalsNearNextWord; i++)
			listOfLists.push_back(makeGlove(i < commaPos ? stemWord(windowList[i]) : windowList[i], mOfTranslates));
		for (; i < windowLen; i++) {
			Words list;
			list.push_back(i < commaPos ? stemWord(windowList[i]) : windowList[i]);
			listOfLists.push_back(list);
		}
		Log::instance().print(1, "Lists of %d word window = ", windowLen);
		// printWordLists(1, listOfLists, "");

		auto start = chrono::steady_clock::now();
		// do vanilla search
		for (int i = 0; i < windowLen; i++)
			mTree.updateWords(i, listOfLists[i]);
		// get all hypothesis of next word
		vector<Words> hypoList = mTree.getWords(windowLen);
		std::chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - start);
		TreeTime += (unsigned)duration.count();
		// printWordLists(2, hypoList, "ofOs_hypo_list = ");

		// do verification
		int verifyLen = min(mVerify, windowLen + 1);
		string prefix;
		for (auto word = windowList.end() - (verifyLen - 1); word < windowList.end(); word++) {
			prefix += *word;
			prefix += ' ';
		}
		for (const Words& hp : hypoList) {
			string s = prefix + hp.back();
			start = chrono::steady_clock::now();
			bool verified = mTree.isContain(s + ' ') || mTree.isContain(s + ", ") || mTree.isContain(s + ". ");
			std::chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - start);
			TreeTime += (unsigned)duration.count();
			if (verified) // verified
				totalVerified += addToVerifiedHypoList(verifiedHypoList, hp);
		}
		// printHypoList(2, verifiedHypoList, "verified_hypo_list = ");
	}
	if (!totalVerified) {
		Log::instance().print(2, "Matches = []\n");
		return string();
	}

	Words windowList = getLastWords(mSeedWordList, min(mWindow, (int)mSeedWordList.size()));
	for (auto hypo1 = verifiedHypoList.begin(); hypo1 < verifiedHypoList.end(); hypo1++)
		for (auto hypo2 = hypo1; ++hypo2 < verifiedHypoList.end(); )
			if (dist(hypo1->words, windowList) < dist(hypo2->words, windowList))
				swap(*hypo1, *hypo2);
		
	int ofMatches = min(totalVerified, mOfMatches);
	int curMatches = 0;
	auto hp = verifiedHypoList.begin();
	do
		curMatches += hp->len;
	while (curMatches < ofMatches && ++hp < verifiedHypoList.end());
	if (hp < verifiedHypoList.end()) {
		hp->len -= curMatches - ofMatches;
		verifiedHypoList.erase(hp + 1, verifiedHypoList.end());
	}
	printHypoList(2, verifiedHypoList, "Matches = ");

	return pickNextWord(verifiedHypoList);
}

int TextGenerator::addToVerifiedHypoList(vector<Hypo>& list, const Words& hp)
{
	int kLen = 0; // sum of length that contain this hp in verified hypo list.
	for (Hypo& verifiedHp : list)
		if (equal(hp.begin(), hp.end(), verifiedHp.words.end() - hp.size()))
			if (verifiedHp.words.size() == hp.size()) {
				++verifiedHp.len;
				return 1;
			} else
				kLen += verifiedHp.len;
	list.push_back(Hypo{hp, 1 - kLen});
	return 1 - kLen;
}

pair<int, int> TextGenerator::dist(const Words& hp, const Words& orig)
{
	int nSame = 0;
	int pattern = 0;
	for (int i = 0; i < (int)hp.size() - 1; i++)
		if (hp.end()[-2 - i] == orig.end()[-1 - i]) {
			++nSame;
			pattern |= 1 << ((int)orig.size() - i);
		}
	return make_pair(nSame, pattern);
}

string TextGenerator::pickNextWord(const vector<Hypo>& hypoList)
{
	unordered_map<string, vector<const Hypo*>> hypoWords;
	for (const Hypo& hypo : hypoList)
		hypoWords[hypo.words.back()].push_back(&hypo);
	// Log::instance().print(1, "Scores of each word\n");
	// Log::instance().print(1, "%-20s: %-10s: %-10s, %-10s, %-10s, %-10s\n", "word", "score", "TransScore", "LenScore", "Contextual", "Originals");

	struct WordScore {
		const string* word;
		double score;

		operator double() const { return score; }
		bool operator<(const WordScore& rhs) const { return score > rhs.score; }
	};

	vector<WordScore> relatedTranslatesBucket;
	ExpCurve expCurve(1, mContextualCoefficient[1], mWindow + 1, mContextualCoefficient[0], mContextualCoefficient[2]);
	for (auto& word : hypoWords) {
		int maxLen = 0;
		double contextualFrequency = 0;
		double originals = 0;
		for (const Hypo* hypo : word.second) {
			int curLen = (int)hypo->words.size();
			maxLen = max(maxLen, curLen);
			double exponentialCoeff = expCurve(curLen) * hypo->len;
			contextualFrequency += exponentialCoeff;
			originals += exponentialCoeff * dist(hypo->words, mSeedWordList).first;
		}
		auto p = mTranslatesBucket.find(word.first);
		double transScore = p == mTranslatesBucket.end() ? 0 : p->second;
		double score = transScore + maxLen + contextualFrequency + originals;
		Log::instance().print(1, "%-20s: %10.4f: %10.4f, %10d, %10.4f, %10.4f\n", word.first.c_str(), score, transScore, maxLen, contextualFrequency, originals);
		relatedTranslatesBucket.push_back(WordScore{&word.first, score});
	}
	int nTopCandidates = min(mPickFromTranslatesBucket, (int)hypoWords.size());
	auto p = relatedTranslatesBucket.begin();
	partial_sort(p, p + nTopCandidates, relatedTranslatesBucket.end());
	return *p[discrete_distribution<>(p, p + nTopCandidates)(mRandomEngine)].word;
}

void TextGenerator::addNextWord(Words& words, const string& nextWord)
{
	if (words.back().back() == '.')
		words.push_back(makeFirstWord(nextWord));
	else
		words.push_back(nextWord);

	Words glove = makeGlove(nextWord, mAddToTranslatesBucket);
	for (const string& word : glove)
		insertToTranslatesBucket(word, nextWord);

	if (!isLastCandidateMostFrequent(words)) { // we couldn't add any comma/stop
		Log::instance().print(2, "we can't add comma due to last word frequency rule.\n");
		return;
	}

	int commaLen = calcCommaLen(words);
	bool shouldAddComma = commaLen >= mWordsPerCommaOrPeriod[0] && (commaLen >= mWordsPerCommaOrPeriod[1] || flipCoin());
	if (shouldAddComma) { // we should add real comma/stop
		int numCommas = 0; // calc number of commas in current sentence.
		for (int i = (int)words.size(); --i >= 0 && words[i].back() != '.'; )
			if (words[i].back() == ',')
				++numCommas;
		// we have to add addCharacter(./,) after last word now.
		Log::instance().print(2, "add real comma/stop");
		words.back() += numCommas >= mCommasPerSentence ? '.' : ',';
	} else
		Log::instance().print(2, "we can't add comma due to WordsPerCommaOrPeriod rule.\n");
}

// check if the last candidates is most frequent in entailData if we add comma/stop.
bool TextGenerator::isLastCandidateMostFrequent(const Words& words) const
{
	printWords(2, words, "Checking if last word is most frequent for hypo -> ");
	double lastFrequency = 0;
	double mostFrequency = 0;
	int lastWindow = (int)words.size() - mLenFrequencyCheckWindow;
	for (int i = 0; i < min(mNofFrequencyCheckCandidates, lastWindow + 1); i++) {
		string candy;
		for (int j = 0; j < mLenFrequencyCheckWindow; j++) {
			candy += stemWord(words[lastWindow - i + j]);
			candy += ' ';
		}
		auto start = chrono::steady_clock::now();
		size_t emptyCount = mTree.calcFrequency(candy);
		candy.insert(candy.end() - 1, ',');
		size_t commaCount = mTree.calcFrequency(candy);
		candy.end()[-2] = '.';
		size_t stopCount = mTree.calcFrequency(candy);
		std::chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - start);
		TreeTime += (unsigned)duration.count();
		size_t totalCount = emptyCount + commaCount + stopCount;
		double freq = totalCount ? (commaCount + stopCount) / (double)totalCount : 0;
		candy.resize(candy.size() - 2);
		Log::instance().print(2, "\"%s,\": %u,\t\"%s.\": %u,\tTotal: %u,\tFreq: %g\n", candy.c_str(), (unsigned)commaCount, candy.c_str(), (unsigned)stopCount, (unsigned)totalCount, freq);
		if (!i)
			lastFrequency = freq;
		else
			mostFrequency = max(mostFrequency, freq);
	}
	return lastFrequency > mostFrequency;
}

Words TextGenerator::makeGlove(string word, int ofTranslates) const
{
	auto start = chrono::steady_clock::now();
	char suffix = '\0';
	if (isCommaOrStop(word)) {
		suffix = word.back();
		word.pop_back();
	}
	Words wordList = mW2vModel.similarByWord(word, ofTranslates);
	wordList.insert(wordList.begin(), word);
	if (suffix)
		for (string& word : wordList)
			word += suffix;
	std::chrono::milliseconds duration = chrono::duration_cast<chrono::milliseconds>(chrono::steady_clock::now() - start);
	GloveTime += (int)duration.count();
	return wordList;
}

void TextGenerator::insertToTranslatesBucket(const string& insertWord, const string& seedWord)
{
	mTranslatesBucket[insertWord] += calcTransscore(seedWord);
}

double TextGenerator::calcTransscore(const string& word) const
{
	auto p = mWordTransScore.find(word);
	return p == mWordTransScore.end() ? mCommonWordCoefficient[1] : p->second;
}

Words TextGenerator::split(const string& text)
{
	Words words;
	const char* s = text.data();
	for (;;) {
		for (; isspace((unsigned char)*s); ++s);
		const char* begin = s;
		for (; *s && !isspace((unsigned char)*s); ++s);
		const char* end = s;
		if (begin == end)
			break;
		words.emplace_back(begin, end);
	}
	return words;
}

string TextGenerator::stemWord(const string& word)
{
	string r;
	for (unsigned char c : word)
		r += (char)tolower(c);
	if (isCommaOrStop(r))
		r.pop_back();
	return r;
}

int TextGenerator::calcCommaLen(const Words& words)
{
	int i = (int)words.size();
	while (--i >= 0 && !isCommaOrStop(words[i]));
	return (int)words.size() - i - 1;
}

bool TextGenerator::isCommaOrStop(const string& word)
{
	char back = word.back();
	return back == ',' || back == '.';
}

string TextGenerator::makeFirstWord(string word)
{
	word[0] = (char)toupper((unsigned char)word[0]);
	return word;
}

Words TextGenerator::getLastWords(const Words& words, int len)
{
	Words last;
	for (int i = len; i; i--)
		last.push_back(words.end()[-i]);
	return last;
}

void TextGenerator::printWords(int logLevel, const Words& words, const char* begin, const char* separator, const char* end)
{
	Log& log = Log::instance();
	log.print(logLevel, "%s", begin);
	for (size_t i = 0; i < words.size(); i++) {
		if (i)
			log.print(logLevel, separator);
		log.print(logLevel, "%s", words[i].c_str());
	}
	log.print(logLevel, "%s", end);
}

void TextGenerator::printWordLists(int logLevel, const vector<Words>& lists, const char* title)
{
	Log& log = Log::instance();
	log.print(logLevel, "%s[", title);
	for (size_t i = 0; i < lists.size(); i++) {
		if (i)
			log.print(logLevel, ", ");
		printWords(logLevel, lists[i], "[", ", ", "]");
	}
	log.print(logLevel, "]\n");
}

void TextGenerator::printHypoList(int logLevel, const vector<Hypo>& list, const char* title)
{
	Log& log = Log::instance();
	log.print(logLevel, "%s[", title);
	for (size_t i = 0; i < list.size(); i++) {
		log.print(logLevel, i ? ", (" : "(");
		printWords(logLevel, list[i].words, "'", " ", "'");
		log.print(logLevel, ", %d)", list[i].len);
	}
	log.print(logLevel, "]\n");
}

TextGenerator::ExpCurve::ExpCurve(double x1, double y1, double x2, double y2, double a) :
	a(a)
{
	double e1 = exp(a * x1);
	double e2 = exp(a * x2);
	k = (y1 - y2) / (e1 - e2);
	b = y1 - (y1 - y2) * e1 / (e1 - e2);
}

void main()
{
	Log& log = Log::instance();
	log.openFile("log.txt", false);
	log.setLogLevel(1, 2);
	log.print(0, "threads %d, mode %d\n", openblas_get_num_threads(), openblas_get_parallel());

	TextGenerator::Params params;
	params.window = 7;
	params.verify = 2;
	params.ofTranslates = 200;
	params.ofMatches = 70;
	params.ofOriginalsNearNextWord = 1;
	params.commasPerSentence = 1;
	params.wordsPerCommaOrPeriod = {4, 4};
	params.commonWordCoefficient = {0.000001, 40, 0.00001};
	params.contextualCoefficient = {0.2, 1, 2.3};
	params.pickFromTranslatesBucket = 2;

	Tree tree;
	string binPath = string(ENTAIL_DATA) + ".bin";
	if (!tree.loadFromFile(binPath.c_str())) {
		if (!tree.build(ENTAIL_DATA, max(params.window + 1, params.verify)))
			return;
		tree.saveToFile(binPath.c_str());
	}

	Word2vec glove(max(params.ofTranslates, params.addToTranslatesBucket));
	binPath = string(GLOVE_MODEL) + ".bin";
	if (!glove.loadFromBinFile(binPath.c_str())) {
		if (!glove.loadFromTextFile(GLOVE_MODEL))
			return;
		glove.saveToBinFile(binPath.c_str());
	}

	try {
		TextGenerator textGenerator(params, glove, tree, COMMON_WORD_FILE);
		for (;;) {
			log.flushFile();
			string seed;
			printf("\nPlease input seed text here:\n");
			getline(cin, seed);
			textGenerator.morphSeed(seed, WORDS_TO_PREDICT);
		}
		//textGenerator.morphSeed("The cat was walking down the street", WORDS_TO_PREDICT);
	} catch (runtime_error& e) {
		log.print(0, e.what());
	}
}
