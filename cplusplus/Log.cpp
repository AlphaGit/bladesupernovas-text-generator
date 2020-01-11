#include <cstdarg>
#include "Log.h"

void Log::openFile(const char* filePath, bool append)
{
	closeFile();
	mFile = fopen(filePath, append ? "r+" : "w");
}

void Log::flushFile()
{
	if (mFile)
		fflush(mFile);
}

void Log::closeFile()
{
	if (mFile)
		fclose(mFile);
	mFile = nullptr;
}

void Log::print(int level, const char* format, ...)
{
	va_list list1, list2;
	va_start(list1, format);
	bool console = level <= mConsoleLevel;
	bool file = level <= mFileLevel && mFile;
	if (console && file)
		va_copy(list2, list1);
	if (console)
		vprintf(format, list1);
	if (file)
		if (console) {
			vfprintf(mFile, format, list2);
			va_end(list2);
		} else
			vfprintf(mFile, format, list1);
	va_end(list1);
}
