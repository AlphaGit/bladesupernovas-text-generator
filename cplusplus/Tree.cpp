#include <algorithm>
#include <cctype>
#include <cstring>
#include <functional>
#include <string>
#include "Log.h"
#include "Tree.h"

void TreeBuilder::addText(string& text)
{
	char* s = const_cast<char*>(text.data());
	for (;;) {
		for (; isspace((unsigned char)*s); ++s);
		if (!*s)
			break;
		const char* begin = s;
		const char* nonAlpha = nullptr;
		for (; *s && !isspace((unsigned char)*s); ++s)
			if (!nonAlpha)
				if (isalpha((unsigned char)*s))
					*s = (char)tolower((unsigned char)*s);
				else
					nonAlpha = s;
		if (!nonAlpha || nonAlpha == s - 1 && (*nonAlpha == ',' || *nonAlpha == '.') && nonAlpha > begin)
			addWord(begin, s);
		else
			clearWords();
	}
}

void TreeBuilder::addWord(const char* begin, const char* end)
{
	if (lastWordsCount) {
		if (lastWordsCount == mScanWindowSz) {
			lastWords.erase(0, lastWords.find(' ') + 1);
			--lastWordsCount;
		}
		lastWords += ' ';
	}
	lastWords.append(begin, end);
	if (++lastWordsCount == mScanWindowSz)
		mRecords.push_back(lastWords);
}

void TreeBuilder::clearWords()
{
	lastWords.clear();
	lastWordsCount = 0;
}

void TreeBuilder::build(vector<string>& records)
{
	sort(mRecords.begin(), mRecords.end());
	mRecords.swap(records);
	mRecords.clear();
	mRecords.shrink_to_fit();
}

// Function to construct tree from entailData
bool Tree::build(const char* filePath, int scanWindowSz)
{
	Log& log = Log::instance();
	log.print(0, "Building Tree from \"%s\"... ", filePath);
	ifstream file(filePath);
	if (!file) {
		log.print(0, "error\n");
		return false;
	}
	TreeBuilder builder(scanWindowSz);
	string line;
	while (getline(file, line))
		builder.addText(line);
	builder.build(mRecords);
	log.print(0, "done\n");
	/*for (const string& s : mRecords)
		puts(s.c_str());*/
	return true;
}

bool Tree::saveToFile(const char* filePath) const
{
	Log& log = Log::instance();
	log.print(0, "Saving Tree to \"%s\"... ", filePath);
	ofstream file(filePath, ios_base::out | ios_base::binary | ios_base::trunc);
	if (!file) {
		log.print(0, "error\n");
		return false;
	}
	uint64_t size = mRecords.size();
	file.write((char*)&size, sizeof(size));
	for (const string& s : mRecords) {
		file.write(s.c_str(), s.size());
		file.put('\0');
	}
	file.close();
	log.print(0, "done\n");
	return true;
}

bool Tree::loadFromFile(const char* filePath)
{
	Log& log = Log::instance();
	log.print(0, "Loading Tree from \"%s\"... ", filePath);
	ifstream file(filePath, ios_base::in | ios_base::binary);
	if (!file) {
		log.print(0, "error\n");
		return false;
	}
	uint64_t size;
	file.read((char*)&size, sizeof(size));
	size = min(size, SIZE_MAX);
	mRecords.clear();
	mRecords.reserve((size_t)size);
	StringReader reader(65536);
	while (reader.read(file))
		for (;;) {
			string s = reader.getString();
			if (s.empty())
				break;
			mRecords.push_back(s);
		}
	log.print(0, "done\n");
	/*ofstream f(string(filePath) + ".txt", ios_base::out | ios_base::trunc);
	for (const string& s : mRecords)
		f << s.c_str() << endl;*/
	return true;
}

void Tree::updateWords(int index, const Words& words)
{
	string searchStr;
	vector<Interval> candidates;
	if (!index)
		for (const string& word : words) {
			Interval r = findInterval(word + ' ');
			if (!r.empty())
				candidates.push_back(r);
		}
	else
		for (Interval interval : mCandidates)
			for (const string& word : words) {
				const string& record = *interval.from;
				size_t i = 0;
				size_t pos = 0;
				while ((pos = record.find(' ', pos + 1)) != string::npos && ++i < index);
				searchStr = record.substr(0, pos) + ' ' + word + ' ';
				Interval r = findInterval(searchStr, interval.from, interval.to);
				if (!r.empty())
					candidates.push_back(r);
			}
	//printCandidates(candidates, "candidates = ");
	mergeCandidates(candidates, index);
}

void Tree::mergeCandidates(vector<Interval>& candidates, int index)
{
	mCandidates.clear();
	if (candidates.empty())
		return;
	sort(candidates.begin(), candidates.end());
	mCandidates.push_back(candidates.front());
	for (Interval candy : candidates) {
		auto& back = mCandidates.back();
		if (candy.from > back.to || !isSameCluster(*back.from, *candy.from, index))
			mCandidates.push_back(candy);
		else if (candy.to > back.to)
			back.to = candy.to;
	}
}

bool Tree::isSameCluster(const string& a, const string& b, int verifyLen)
{
	const char* s1 = a.c_str();
	const char* s2 = b.c_str();
	for (; *s1 == *s2; s1++, s2++)
		if (!*s1)
			return !verifyLen;
		else if (*s1 == ' ' && !verifyLen--)
			return true;
	return false;
}

void Tree::printCandidates(const vector<Interval>& candidates, const char* title) const
{
	printf("%s[", title);
	for (size_t i = 0; i < candidates.size(); i++) {
		if (i)
			printf(", ");
		printf("(%u - %u)", (unsigned)(candidates[i].from - &mRecords[0]), (unsigned)(candidates[i].to - &mRecords[0]));
	}
	printf("]\n");
}

// return word list of vanila serarch ex. [[down the street], [up the street], [down the stair], ...]
// here predicted next word is [street, stair, ...]
vector<Words> Tree::getWords(int index) const
{
	vector<Words> result;
	for (Interval interval : mCandidates)
		for (const string& sequence : interval) {
			Words words;
			size_t wordBegin = 0;
			size_t wordEnd;
			for (;;) {
				wordEnd = sequence.find(' ', wordBegin + 1);
				if (wordEnd == string::npos) {
					wordEnd = sequence.size();
					break;
				}
				if (words.size() == index)
					break;
				words.push_back(sequence.substr(wordBegin, wordEnd - wordBegin));
				wordBegin = wordEnd + 1;
			}
			if (words.size() == index && (sequence[wordEnd - 1] != ',' && sequence[wordEnd - 1] != '.' || wordBegin < --wordEnd)) {
				words.push_back(sequence.substr(wordBegin, wordEnd - wordBegin));
				result.push_back(words);
			}
		}
	return result;
}

Tree::Interval Tree::findInterval(const string& searchStr, const string* begin, const string* end)
{
	auto range = equal_range(begin, end, searchStr, bind(compareStr, placeholders::_1, placeholders::_2, searchStr.size()));
	return Interval{range.first, range.second};
}

bool Tree::compareStr(const string& s1, const string& s2, size_t length)
{
	return s1.compare(0, length, s2, 0, length) < 0;
}

size_t Tree::calcFrequency(const string& searchStr) const
{
	Interval interval = findInterval(searchStr);
	return interval.to - interval.from;
}

// calcuate the most frequent next word of a SearchStr ex. "down the " -> "path, 15"
pair<string, size_t> Tree::calcMostFrequentNextWord(const string& searchStr) const
{
	size_t nextWordPos = searchStr.size();
	Interval interval = findInterval(searchStr);
	const char* curWord;
	size_t curWordSize = 0;
	const char* maxWord;
	size_t maxWordSize = 0;
	size_t curCount = 0;
	size_t maxCount = 0;
	for (const string& sequence : interval) {
		char c;
		if (!curWordSize || sequence.compare(nextWordPos, curWordSize, curWord) || (c = sequence[nextWordPos + curWordSize]) && c != ' ') {
			if (curCount > maxCount) {
				maxCount = curCount;
				maxWord = curWord;
				maxWordSize = curWordSize;
			}
			curWord = sequence.c_str() + nextWordPos;
			size_t pos = sequence.find(' ', nextWordPos + 1);
			curWordSize = (pos == string::npos ? sequence.size() : pos) - nextWordPos;
			curCount = 1;
		} else
			++curCount;
	}
	return curCount > maxCount
		? make_pair(string(curWord, curWordSize), curCount)
		: make_pair(string(maxWord, maxWordSize), maxCount);
}
