#pragma once
#include <stdio.h>

class Log {
public:
	static Log& instance() { static Log log; return log; }
	~Log() { closeFile(); }

	void setLogLevel(int consoleLevel, int fileLevel) { mConsoleLevel = consoleLevel; mFileLevel = fileLevel; }
	void openFile(const char* filePath, bool append);
	void flushFile();
	void closeFile();
	void print(int level, const char* format, ...);

private:
	Log() {}

	int mConsoleLevel = 0;
	int mFileLevel = 0;
	FILE* mFile = nullptr;
};
