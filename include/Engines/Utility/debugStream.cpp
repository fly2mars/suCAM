// debugstream.cpp
//
// Copyright (c) 2003 Philip Romanik, Amy Muntz
//
// Permission to use, copy, modify, distribute, and sell this software and
// its documentation for any purpose is hereby granted without fee, provided
// that (i) the above copyright notices and this permission notice appear in
// all copies of the software and related documentation, and (ii) the names
// of Philip Romanik and Amy Muntz may not be used in any advertising or
// publicity relating to the software without the specific, prior written
// permission of Philip Romanik and Amy Muntz.
//
// Use of this software and/or its documentation will be deemed to be
// acceptance of these terms.
//
// THE SOFTWARE IS PROVIDED "AS-IS" AND WITHOUT WARRANTY OF ANY KIND,
// EXPRESS, IMPLIED OR OTHERWISE, INCLUDING WITHOUT LIMITATION, ANY
// WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
//
// IN NO EVENT SHALL PHILIP ROMANIK OR AMY MUNTZ BE LIABLE FOR
// ANY SPECIAL, INCIDENTAL, INDIRECT OR CONSEQUENTIAL DAMAGES OF ANY KIND,
// OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
// WHETHER OR NOT ADVISED OF THE POSSIBILITY OF DAMAGE, AND ON ANY THEORY OF
// LIABILITY, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
// OF THIS SOFTWARE.
//
//
// General-purpose debug stream, like std::cout


#include "debugStream.h"
#include <time.h>


// Ruler
//       1         2         3         4         5         6    6
//345678901234567890123456789012345678901234567890123456789012345



// *****************
// *               *
// *  suDebugSink  *
// *               *
// *****************

suDebugSink::suDebugSink () : enableHeader_(false) {}

std::string suDebugSink::standardHeader ()
{
  std::string header;

  // Fetch the current time
  time_t now = time(0);
  header += ctime (&now);
  header.erase (header.length()-1, 1); // Remove newline written
  header += ": ";

  return header;
}


// *********************
// *                   *
// *  suDebugSinkNull  *
// *                   *
// *********************

suDebugSinkNull suDebugSinkNull::sOnly = suDebugSinkNull ();

suDebugSinkNull::suDebugSinkNull () {}



// ************************
// *                      *
// *  suDebugSinkConsole  *
// *                      *
// ************************

suDebugSinkConsole suDebugSinkConsole::sOnly = suDebugSinkConsole ();

suDebugSinkConsole::suDebugSinkConsole  () {}
suDebugSinkConsole::~suDebugSinkConsole () { flush();}


void suDebugSinkConsole::write (const std::string& str)
{
  buffer_ += str;
  flush ();
}

void suDebugSinkConsole::write (int c)
{
  buffer_ += (char)c;
  if (c == '\n')
    flush ();
}

void suDebugSinkConsole::display (const std::string& str)
{
  std::cout << str;
}

void suDebugSinkConsole::flush ()
{
  if (buffer_.empty())
    return;

  if (enableHeader_)
    buffer_ = header() + buffer_;

  // Add a trailing newline if we don't have one
  // (we need this when we shut down)
  if (buffer_[buffer_.length()-1] != '\n')
    buffer_ += '\n';

  display (buffer_);
  buffer_.clear ();
}


// *********************
// *                   *
// *  suDebugSinkFile  *
// *                   *
// *********************

suDebugSinkFile suDebugSinkFile::sOnly = suDebugSinkFile ();

suDebugSinkFile::suDebugSinkFile  () {}
suDebugSinkFile::~suDebugSinkFile () { flush();}

void suDebugSinkFile::setFile (const std::string& file)
{
  flush();
  file_ = file;
}

void suDebugSinkFile::display (const std::string& str)
{
  if (file_.empty())
    return;

  // Open the file in append mode. The dtor will close
  // the file for us.
  std::ofstream output (file_.c_str(), std::ios_base::app);
  if (!output)
    return;    // The file could not be opened. Exit

  output << str;
}



// **********************
// *                    *
// *  suDebugStringBuf  *
// *                    *
// **********************

suDebugStringBuf<char> debugstream;

std::ostream cdebug (&debugstream);

