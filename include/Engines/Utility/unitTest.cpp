// unittest.cpp
//
// Simple unit test framework.

#include "unitTest.h"
#include "timing.h"

#include <math.h>
#include <stdio.h>

/*!suUnitTestFunction  */
// *                     
suUnitTestFunction::suUnitTestFunction (const std::string& name)
: result_ (eNotRun), name_ (name), verbose_ (false), elapsed_ (0),bIfRun_(true)
{}


void suUnitTestFunction::run (bool verbose)
{
  std::string error;
  verbose_ = verbose;

  // Run the test
  if (!needRun())
  {
	  result_ = eNotRun;
	  return;
  }
  if (verbose) 
    std::cout << "Running " << name_.c_str() << std::endl;
  result_ = eRunning;
 
  suElapsedTime time;
  try {
    test ();
  }
  catch (const std::exception& ex) {
    // We caught an STL exception
    error = std::string("Exception '") + ex.what() + "' caught";
    if (verbose)
      std::cout << error << " in " << name_.c_str() << std::endl;
    addMessage (error);
    result_ = eFailure;
  }
  catch (...) {
    // We caught an unknown exception
    error = "Unknown exception caught";
    if (verbose)
      std::cout << error << " in " << name_.c_str() << std::endl;
    addMessage (error);
    result_ = eFailure;
  }
  elapsed_ = time.sec ();

  // Make sure the test() function set a result or set eUnknown
  if (result_ != eSuccess && result_ != eFailure)
    result_ = eUnknown;

  if (verbose_) {
    std::cout << "  Result of " << name_.c_str() << " is " 
              << resultString().c_str() << " (" << elapsed_ 
              << " sec)" << std::endl;
    if (message_.size() > 0)
      std::cout << "  Messages: " << message_.c_str() 
                << std::endl;
  }
}


bool suUnitTestFunction::verify (bool state, const std::string& message)
{
  if (!state) {
    result_ = eFailure;
    addMessage (message);
    if (verbose_) 
      std::cout << " FAILURE " << name_.c_str() << " : " 
                << message.c_str() << std::endl;
  }
  else if (result_ != eFailure)
    // Make sure we mark the unit test success, if possible.
    result_ = eSuccess;
  return state;
}

bool suUnitTestFunction::verifyFloat (double d1, double d2)
{
  double delta = fabs (d1-d2);
  if (delta > 1.e-5) {
    char buffer[128];
    sprintf (buffer, "%.11f != %.11f", d1, d2);
    return verify (false, buffer);
  }

  return verify (true);
}


void suUnitTestFunction::addMessage (const std::string& message)
{
  if (message_.size() > 0) message_ += "\n";
  message_ += message;
}


// Not a const reference because it isn't safe
std::string suUnitTestFunction::resultString () const
{
  switch (result_) {
  case eNotRun:
    return "Not Run";
  case eRunning:
    return "Running";
  case eUnknown:
    return "Unknown";
  case eSuccess:
    return "Success";
  case eFailure:
    return "***** Failure *****";
  default:
    break;
  }

  return "Unknown Result";
}


// ****************
// *              *
// *  suUnitTest  *
// *              *
// ****************
//

suUnitTest* suUnitTest::sOnly_ = 0;

suUnitTest& suUnitTest::gOnly ()
{
  if (!sOnly_)  sOnly_ = new suUnitTest ();
  return *sOnly_;
}


suUnitTest::suUnitTest () : start_ (0), stop_ (0)
{}


void suUnitTest::addTest (const std::string& /*name*/, 
                          suUnitTestFunction* test)
{
  // Keep track of this unit test object to run
  tests_.push_back (test);
}

bool suUnitTest::run (bool verbose)
{
  bool state = true;
  start_ = time(0);

  for (unsigned int i=0; i<tests_.size(); i++) {
    // Fetch the next test to run and run it
    suUnitTestFunction* test = tests_[i];
    test->run (verbose);
    if (test->result() != suUnitTestFunction::eSuccess) 
      state = false;
  }

  stop_ = time(0);
  return state;
}


const suUnitTestFunction* suUnitTest::retrieve (int index) const
{
  if (index < 0 || index >= size()) return 0;
  return tests_[index];
}


void suUnitTest::dumpResults (std::ostream& out)
{
  int nSuccess = 0;
  int nFailed  = 0;
  int nOther   = 0;

  out << "Unit Test started at  " << ctime(&start_) << std::endl;
  out << "Unit Test finished at " << ctime(&stop_) << std::endl;

  for (unsigned int i=0; i<tests_.size(); i++) {
    suUnitTestFunction* test = tests_[i];

    switch (test->result()) {
    case suUnitTestFunction::eSuccess:
      nSuccess++;
      break;
    case suUnitTestFunction::eFailure:
      nFailed++;
      break;
    default:
      nOther++;
      break;
    };

    out << "Test " << i+1 << ": " << test->resultString().c_str() 
        << " : " << test->name().c_str() << " : ";
    if (test->description().size() > 0)
      out << test->description().c_str();
    out << " : " << test->elapsed() << " sec" << std::endl;
    if (test->message().size() > 0)
      out << "  Messages: " << std::endl 
          << test->message().c_str() << std::endl;
  }

  out << std::endl << std::endl;
  out << "Passed: " << nSuccess << ", Failed: " << nFailed 
      << ", Other: " << nOther << std::endl;
}
