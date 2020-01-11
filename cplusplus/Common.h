#pragma once
#include <fstream>
#include <string>
#include <vector>

using namespace std;

typedef vector<string> Words;

class StringReader {
public:
	StringReader(size_t size) : mBuffer(size), mDataBegin(mBuffer.data()), mDataEnd(mDataBegin) {}
	bool read(ifstream& file);
	string getString();

private:
	vector<char> mBuffer;
	char* mDataBegin;
	char* mDataEnd;
};
