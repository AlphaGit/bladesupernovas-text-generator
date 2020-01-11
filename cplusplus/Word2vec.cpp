#include <algorithm>
#include <numeric>
#include <fstream>
#include "OpenBLAS/cblas.h"
#include "Log.h"
#include "Word2vec.h"

bool Word2vec::loadFromTextFile(const char* filePath)
{
	Log& log = Log::instance();
	log.print(0, "Loading w2v model from \"%s\"... ", filePath);
	mWords.clear();
	mWordIndexes.clear();
	mValues.clear();
	ifstream file(filePath);
	if (!file) {
		log.print(0, "error\n");
		return false;
	}
	/*ofstream outFile((string(filePath) + ".bin").c_str(), ios_base::binary | ios_base::out | ios_base::trunc);
	if (!outFile)
		return false;
	outFile.seekp(8);*/
	int wordsCount = 0;
	mPlanesCount = 0;
	file >> wordsCount >> mPlanesCount;
	file.clear();
	mValues.reserve((size_t)wordsCount * mPlanesCount);
	mWords.reserve(wordsCount);
	vector<double> values;
	double norm;
	string s;
	bool isWordRead = false;
	while (file >> s) {
		if (isWordRead) {
			bool isNextWordRead = false;
			try {
				double value = stod(s);
				values.push_back(value);
				norm += value * value;
			} catch (invalid_argument) {
				if (mPlanesCount) {
					log.print(0, "error converting \"%s\"\n", s.c_str());
					break;
				}
				mPlanesCount = (int)values.size();
				isNextWordRead = true;
			}
			if ((int)values.size() == mPlanesCount) {
				norm = sqrt(norm);
				for (double value : values)
					mValues.push_back((Value)(value / norm));
				/*outFile.write((char*)mValues.data(), values.size() * sizeof(Value));
				mValues.clear();*/
				isWordRead = false;
			}
			if (!isNextWordRead)
				continue;
		}
		mWords.push_back(s);
		isWordRead = true;
		values.clear();
		norm = 0;
	}
	mWords.shrink_to_fit();
	mValues.shrink_to_fit();
	mWordIndexes.reserve(mWords.size());
	for (string& word : mWords)
		mWordIndexes.emplace(&word, (Index)mWordIndexes.size());

	/*for (auto& word : words) {
		outFile.write(word.data(), word.size());
		outFile << '\0';
	}
	outFile.seekp(0);
	wordsCount = (unsigned)words.size();
	outFile.write((char*)&wordsCount, 4);
	outFile.write((char*)&mPlanesCount, 4);*/
	log.print(0, "done, %u words, %u planes\n", (int)mWords.size(), mPlanesCount);
	return true;
}

bool Word2vec::loadFromBinFile(const char* filePath)
{
	Log& log = Log::instance();
	log.print(0, "Loading w2v model from \"%s\"... ", filePath);
	mWords.clear();
	mWordIndexes.clear();
	mValues.clear();
	ifstream file(filePath, ios_base::in | ios_base::binary);
	if (!file) {
		log.print(0, "error\n");
		return false;
	}
	int wordsCount;
	file.read((char*)&wordsCount, 4);
	file.read((char*)&mPlanesCount, 4);

	size_t size = (size_t)wordsCount * mPlanesCount;
	mValues.reserve(size);
	while (size) {
		char buf[65536];
		size_t toRead = min(sizeof(buf) / sizeof(Value), size);
		file.read(buf, toRead * sizeof(Value));
		mValues.insert(mValues.end(), (Value*)buf, (Value*)buf + toRead);
		size -= toRead;
	}

	mWords.reserve(wordsCount);
	mWordIndexes.reserve(wordsCount);
	StringReader reader(65536);
	while (reader.read(file))
		for (;;) {
			string s = reader.getString();
			if (s.empty())
				break;
			mWords.push_back(s);
			mWordIndexes.emplace(&mWords.back(), (Index)mWordIndexes.size());
		}
	log.print(0, "done, %u words, %u planes\n", (int)mWords.size(), mPlanesCount);
	return true;
}

bool Word2vec::saveToBinFile(const char* filePath) const
{
	Log& log = Log::instance();
	log.print(0, "Saving w2v model to \"%s\"... ", filePath);
	ofstream file(filePath, ios_base::binary | ios_base::out | ios_base::trunc);
	if (!file) {
		log.print(0, "error\n");
		return false;
	}
	int wordsCount = (int)mWords.size();
	file.write((char*)&wordsCount, 4);
	file.write((char*)&mPlanesCount, 4);
	for (Value value : mValues)
		file.write((char*)&value, sizeof(value));

	for (const string& word : mWords) {
		file.write(word.data(), word.size());
		file << '\0';
	}
	file.close();
	log.print(0, "done\n");
	return true;
}

vector<string> Word2vec::similarByWord(const string& word, int count)
{
	vector<string> r;
	const Index* words = findWordInCache(word, count);
	if (!words) {
		auto pWord = mWordIndexes.find(&word);
		if (pWord == mWordIndexes.end())
			return r;
		int cacheCount = max(count, mCacheSimilarWordsCount);
		words = calcSimilar(pWord->second, cacheCount);
		putWordInCache(mWords[pWord->second], words, cacheCount);
	}
	r.reserve(count);
	for (int i = 0; i < count; i++)
		r.push_back(mWords[words[i]]);
	return r;
}

const Word2vec::Index* Word2vec::calcSimilar(Index word, int count)
{
	const Value* wordValues = &mValues[word * (size_t)mPlanesCount];
	mProduct.resize(mWords.size());
	cblas_sgemv(CblasRowMajor, CblasNoTrans, (int)mWords.size(), mPlanesCount, 1., mValues.data(), mPlanesCount, wordValues, 1, 0., const_cast<Value*>(mProduct.data()), 1);
	mIndexes.resize(mWords.size());
	iota(mIndexes.begin(), mIndexes.end(), 0);
	auto end = mIndexes.begin() + count + 1;
	partial_sort(mIndexes.begin(), end, mIndexes.end(), [this](Index lhs, Index rhs) {
		return mProduct[lhs] > mProduct[rhs];
	});
	auto same = find(mIndexes.begin(), end, word);
	if (same != end)
		copy(same + 1, end, same);
	return mIndexes.data();
}

void Word2vec::putWordInCache(const string& word, const Index* similarWords, int count)
{
	vector<Index>& p = mCache[&word];
	p.clear();
	p.insert(p.begin(), similarWords, similarWords + count);
}

const Word2vec::Index* Word2vec::findWordInCache(const string& word, int count)
{
	auto p = mCache.find(&word);
	if (p == mCache.end())
		return nullptr;
	else if ((int)p->second.size() < count) {
		Log::instance().print(0, "Too little similar words in cache: %d instead of %d\n", (int)p->second.size(), count);
		return nullptr;
	} else
		return p->second.data();
}
