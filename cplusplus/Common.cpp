#include <cstring>
#include "Common.h"

bool StringReader::read(ifstream& file)
{
	size_t dataSize = mDataEnd - mDataBegin;
	memmove(mBuffer.data(), mDataBegin, dataSize);
	mDataBegin = mBuffer.data();
	mDataEnd = mDataBegin + dataSize;
	size_t freeSize = mBuffer.size() - dataSize;
	if (!freeSize)
		return false;
	file.read(mDataEnd, freeSize);
	if (!file.gcount())
		return false;
	mDataEnd += file.gcount();
	return true;
}

string StringReader::getString()
{
	char* strEnd = (char*)memchr(mDataBegin, 0, mDataEnd - mDataBegin);
	if (!strEnd)
		return string();
	string s(mDataBegin, strEnd - mDataBegin);
	mDataBegin = strEnd + 1;
	return s;
}
