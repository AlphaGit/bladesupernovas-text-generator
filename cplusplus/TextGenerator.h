#pragma once
#include <array>
#include <random>
#include <unordered_map>
#include "Tree.h"
#include "Word2vec.h"

class TextGenerator {
public:

	struct Params {
		int window = 4;
		int verify = 2;
		int ofTranslates = 2;
		int ofMatches = 1;
		int ofOriginalsNearNextWord = 0;
		int commasPerSentence = 2;
		array<int, 2> wordsPerCommaOrPeriod = {4, 7};
		array<double, 3> commonWordCoefficient = {1, 100, 0.0011};
		array<double, 3> contextualCoefficient = {1, 0.000001, 0.0002};
		int pickFromTranslatesBucket = 2;               // how many words we should pick from a bucket for softmax.
		int addToTranslatesBucket = 30;                 // how many gloves of a word we should insert to translatesBucket.
		int nofFrequencyCheckCandidates = 8;            // how many last candidates we should check for frequency.
		int lenFrequencyCheckWindow = 2;                // length of frequency check window.
	};

	TextGenerator(const Params& params, Word2vec& model, Tree& tree, const char* commonWordsFilePath);
	void morphSeed(const string& seed, int length);

private:

	class Hypo {
	public:
		Words words;
		int len;
	};

	class ExpCurve {
	public:
		ExpCurve(double x1, double y1, double x2, double y2, double a);
		double operator()(double x) const { return k * exp(a * x) + b; }

	private:
		double a, k, b;
	};

	bool loadCommonWord(const char* filePath);
	Words makeGlove(string word, int ofTranslates) const;
	void insertToTranslatesBucket(const string& insertWord, const string& seedWord);
	double calcTransscore(const string& word) const;
	string predict(const Words& inputSeed);
	static int addToVerifiedHypoList(vector<Hypo>& list, const Words& hp);
	static pair<int, int> dist(const Words& hp, const Words& orig);
	string pickNextWord(const vector<Hypo>& hypoList);
	void addNextWord(Words& words, const string& nextWord);
	bool isLastCandidateMostFrequent(const Words& words) const;
	bool flipCoin() { return mRandomBits() > 0; }

	static Words split(const string& text);
	static string stemWord(const string& word);
	static int calcCommaLen(const Words& words);
	static bool isCommaOrStop(const string& word);
	static string makeFirstWord(string word);
	static Words getLastWords(const Words& words, int len);
	static void printWords(int logLevel, const Words& words, const char* begin, const char* separator = " ", const char* end = "\n");
	static void printWordLists(int logLevel, const vector<Words>& lists, const char* title);
	static void printHypoList(int logLevel, const vector<Hypo>& list, const char* title);

	Word2vec& mW2vModel;
	Tree& mTree;
	unordered_map<string, double> mWordTransScore;

	int mWindow;
	int mVerify;
	int mOfTranslates;
	int mOfMatches;
	int mOfOriginalsNearNextWord;
	int mCommasPerSentence;
	array<int, 2> mWordsPerCommaOrPeriod;
	array<double, 3> mCommonWordCoefficient;
	array<double, 3> mContextualCoefficient;
	int mPickFromTranslatesBucket;                   // how many words we should pick from a bucket for softmax.
	int mAddToTranslatesBucket;                      // how many gloves of a word we should insert to translatesBucket.
	int mNofFrequencyCheckCandidates;                // how many last candidates we should check for frequency.
	int mLenFrequencyCheckWindow;                    // length of frequency check window.

	unordered_map<string, double> mTranslatesBucket; // translatesbucket to contain all translates of words up to now.
	Words mSeedWordList;
	mt19937_64 mRandomEngine;
	independent_bits_engine<mt19937_64, 1, mt19937_64::result_type> mRandomBits;
};