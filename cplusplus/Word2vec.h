#pragma once
#include <deque>
#include <unordered_map>
#include "Common.h"

class Word2vec {
public:
	Word2vec(int cacheSimilarWordsCount) : mCacheSimilarWordsCount(cacheSimilarWordsCount) {}
	bool loadFromTextFile(const char* filePath);
	bool loadFromBinFile(const char* filePath);
	bool saveToBinFile(const char* filePath) const;
	Words similarByWord(const string& word, int count);

private:
	typedef float Value;
	typedef int Index;

	const Index* calcSimilar(Index word, int count);
	void putWordInCache(const string& word, const Index* similarWords, int count);
	const Index* findWordInCache(const string& word, int count);

	struct Hash {
		auto operator()(const string* word) const {
			return hash<string>()(*word);
		}
	};

	struct Equal {
		bool operator()(const string* word1, const string* word2) const {
			return *word1 == *word2;
		}
	};

	int mPlanesCount;
	vector<string> mWords;
	unordered_map<const string*, Index, Hash, Equal> mWordIndexes;
	vector<Value> mValues;

	int mCacheSimilarWordsCount;
	unordered_map<const string*, vector<Index>, Hash, Equal> mCache;
	vector<Value> mProduct;
	vector<Index> mIndexes;
};