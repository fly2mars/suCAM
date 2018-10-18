#ifndef _debugstream_h_
#define _debugstream_h_

// debugstream.h
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
//  General-purpose debug stream, like std::cout


#include <ostream>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>


// *****************
// *               *
// *  suDebugSink  *
// *               *
// *****************
//
// suDebugSink and derived classes are used to specify the behavior of what
// happens to output sent to the cdebug stream. A suDebugStringBuf<>
// object is defined in this file which derives from std::basic_stringbuf.
// This object is used when constructing cdebug (which is a std::ostream
// object). The stream objects can definitely get confusing. The objects
// presented here show an easy way to hook into streams for your own
// purposes. There are more elegant ways but they require more knowledge
// about streams than most people need to worry about.
//
// suDebugSink        Abstract base class that defines a simple
//                    debugging stream.
// suDebugSinkNull    Does nothing
// suDebugSinkConsole Writes debugging information to std::cout
// suDebugSinkFile    Writes debugging information to the
//                    specified file.
//
// Common overrides (of suDebugSink)
//
//   header(). Override to change the standard header that is
//             displayed, if enabled

class suDebugSink
{
public:
  suDebugSink ();

  virtual void write (const std::string& str) = 0;
  // Write a string to our debugging sink;

  virtual void write (int c) = 0;
  // Write a character to our debugging sink. Usually called from
  // a std::basic_stringbuf derived object as characters are received.

  virtual void flush () {}
  // flush any stored information if possible for this type of sink.

  virtual std::string header () { return standardHeader();}
  // By default, we emit our standard header when headers are enabled

  void showHeader (bool state) {  enableHeader_ = state;}
  // Set the state of whether a header is written

protected:
  std::string standardHeader ();
  // The standard header consists of the current time

  bool enableHeader_; // true to write header whenever buffer is flushed
};


// *********************
// *                   *
// *  suDebugSinkNull  *
// *                   *
// *********************
//
// Null sink

class suDebugSinkNull : public suDebugSink
{
public:
  static suDebugSinkNull sOnly;

  virtual void write (const std::string& /*str*/) {}
  virtual void write (int /*c*/) {}

private:
  suDebugSinkNull ();
};


// ************************
// *                      *
// *  suDebugSinkConsole  *
// *                      *
// ************************
//
// Console sink. Data is written to std::cout
//
// Common overrides
//
//   display(). Override to change the output source. Default is std::cout.
//              See suDebugSinkFile for an example of this.

class suDebugSinkConsole : public suDebugSink
{
public:
  static suDebugSinkConsole sOnly;

  virtual void write (const std::string& str);
  virtual void write (int c);
  virtual void flush ();

protected:
  virtual void display (const std::string& str);
  // Output the string. Derived classes can override this

  suDebugSinkConsole ();
  virtual ~suDebugSinkConsole ();

  std::string buffer_;
};


// *********************
// *                   *
// *  suDebugSinkFile  *
// *                   *
// *********************
//
// File sink

class suDebugSinkFile : public suDebugSinkConsole
{
public:
  static suDebugSinkFile sOnly;

  void setFile (const std::string& file);
  // Set/change our file name. The stream is flushed before the
  // file name is changed.

private:
  virtual void display (const std::string& str);

  suDebugSinkFile ();
  virtual ~suDebugSinkFile ();

  std::string file_;
};





// **********************
// *                    *
// *  suDebugStringBuf  *
// *                    *
// **********************
//
// We need to derive a class from std::basic_stringbuf<> to intercept
// characters for our debugging sinks. suDebugStringBuf bridges the
// gap by intercepting stream characters by overriding overflow() and
// passing the characters to the current sink

template<class T, class Tr = std::char_traits<T>, class A = std::allocator<T> >
class suDebugStringBuf : public std::basic_stringbuf<T, Tr, A>
{
public:
  suDebugStringBuf (suDebugSink& s = suDebugSinkNull::sOnly) : sink_ (&s) {}
  ~suDebugStringBuf () { sink_->flush();}

  typedef typename std::basic_stringbuf<T, Tr, A>::int_type int_type;

  int_type overflow (int_type c) {
    if (c != traits_type::eof())
      sink_->write (c);
    return traits_type::not_eof(c);
  }

  void sink (suDebugSink& s) { sink_ = &s;}
  // Change our sink

private:
  suDebugStringBuf (const suDebugStringBuf&);  // Do not allow copies
  suDebugStringBuf& operator= (const suDebugStringBuf&);  // Do not allow copies

  suDebugSink* sink_;
};


// Our global instance we will use to write debugging information
// You can use cdebug just like std::cout. The default sink is
// suDebugSinkNull so you'll need to set it to something, before
// using cdebug, ex:
//     debugstream.sink (suDebugSinkConsole::sOnly);

extern suDebugStringBuf<char> debugstream;
extern std::ostream cdebug;


#endif // _debugstream_h_
