#pragma once
#include "Common.h"

using namespace std;

class TreeBuilder {
public:
	TreeBuilder(int scanWindowSz) : mScanWindowSz(scanWindowSz) {}
	void addText(string& text);
	void build(vector<string>& records);

private:
	void addWord(const char* begin, const char* end);
	void clearWords();

	int mScanWindowSz;
	vector<string> mRecords;
	string lastWords;
	int lastWordsCount = 0;
};

class Tree {
public:
	bool build(const char* filePath, int scanWindowSz);
	//void build(const Words& text, int scanWindowSz);
	bool saveToFile(const char* filePath) const;
	bool loadFromFile(const char* filePath);
	void updateWords(int index, const Words& words);
	vector<Words> getWords(int index) const;
	bool isContain(const string& searchStr) const { return !findInterval(searchStr).empty(); }
	size_t calcFrequency(const string& searchStr) const;
	pair<string, size_t> calcMostFrequentNextWord(const string& searchStr) const;

private:
	struct Interval {
		const string *from, *to;

		bool empty() const { return from == to;  }
		bool operator<(const Interval& rhs) const { return from < rhs.from || from == rhs.from && to < rhs.to; }
		const string* begin() const { return from; }
		const string* end() const { return to; }
	};

	Interval findInterval(const string& searchStr) const { return findInterval(searchStr, &*mRecords.begin(), &mRecords.end()[-1] + 1); }
	static Interval findInterval(const string& searchStr, const string* begin, const string* end);
	static bool compareStr(const string& record, const string& key, size_t length);
	void mergeCandidates(vector<Interval>& candidates, int index);
	static bool isSameCluster(const string& a, const string& b, int verifyLen);
	void printCandidates(const vector<Interval>& candidates, const char* title) const;

	vector<string> mRecords; // all hypo records made from entailData for fast search of scanWindow or verification
	vector<Interval> mCandidates;
};