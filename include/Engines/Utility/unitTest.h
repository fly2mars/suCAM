#ifndef _unittest_h_
#define _unittest_h_

// unittest.h
//
//
// Simple unit test for suImage Lib.

#include <string>
#include <vector>
#include <iostream>

#include <time.h>


/*!\class  suUnitTestFunction
*\brief  
suUnitTestFunction is the base class for all unit test
functions. The macros defined at the bottom of this file will
construct objects derived from suUnitTestFunction.
<pre>
When you write a unit test function, it executes as a member
or an object derived from suUnitTestFunction.  Useful 
functions:

   VERIFY(condition)       A macro wrapped around verify(). If
                           condition resolves to false, the
                           unit test will fail.
   verifyFloat (d1,d2);    Verifies that d1= d2, within a
                           small value delta.  If this 
                           condition is false, the unit test 

                           will fail.
   VERIFYFLOAT(d1,d2);     Same as verifyFlot() to match the
                           look of VERIFY().
   addMessage (string);    Adds the string to our internal
                           message string.

 You should call VERIFY() or VERIFYFLOAT() at least once in 
 each unit test function.  If you don't the result state of
 the function will be eUnknown.
 </pre>
*/

class suUnitTestFunction
{
public:
  suUnitTestFunction (const std::string& name);

  enum eResult {eNotRun, eRunning, eUnknown, eSuccess, eFailure};
  // Each unit test has a result, even if the user never sets it

  const std::string& name         () const { return name_;}
  eResult            result       () const { return result_;}
  double             elapsed      () const { return elapsed_;}
  const std::string& message      () const { return message_;}
  const std::string& description  () const
  { return description_;}
  std::string        resultString () const;

  void setDescription (const std::string& s) { description_ = s;}
  //!< Set the description of this test function

  void run (bool verbose = false);
  //!< Run this unit test. Called by the unit test framework

  void setIfRun(bool bIfRun){bIfRun_ = bIfRun;}
  //!< Set by user, to avoid unit running during test process, just to save time.

  bool needRun(){return bIfRun_;}
  //!< Return if this unit need to run.


protected:
  virtual void test() = 0;
  //!< All unit tests define this function to perform a single test

  bool verify (bool state, const std::string& message="");
  //!< Fails test if state is false. Used by VERIFY() macro

  bool verifyFloat (double d1, double d2);
  //!< Verifies d1=d2, within a value delta. Used by VERIFYFLOAT()

  void addMessage (const std::string& message);
  //!< Adds the message string to our messages

  bool         verbose_;     //!< true for verbose output

  eResult      result_;      //!< Result of this unit test
  std::string  name_;        //!< Unit test name (must be unique)
  std::string  description_; //!< Description of function
  std::string  message_;     //!< Message, usual a failure message
  double       elapsed_;     //!< Execution time, in seconds
  bool         bIfRun_;      //!< If run in unit test process
};



/*!\class suUnitTest
*\brief singlinton class for unit test function
*/

class suUnitTest
{
public:
  static suUnitTest& gOnly ();
  //!< The only instance of this object we create

  bool run (bool verbose = false);
  //!< Run all the unit tests. Returns true if all tests are ok

  void dumpResults (std::ostream& out);
  //!< Dump results to specified stream

  int size () const { return static_cast<int>(tests_.size());}
  const suUnitTestFunction* retrieve (int index) const;
  //!< Retrieves the specific test, or NULL if invalid index


  void addTest (const std::string& name, suUnitTestFunction* test);
  //!< Used by our macro to add another unit test

private:
  suUnitTest ();  //!< We will only have one instance, gOnly()

  static suUnitTest* sOnly_;  //!< Points to our only instance

  std::vector<suUnitTestFunction*> tests_; //!< Array of tests
  time_t start_, stop_;                    //!< Start, stop time
};



/*A def "semi class structure" for writing simply unit test function*/

// This might look difficult, but it creates a unique class,
// derived from suUnitTestFunction. A static instance is also
// created which will add itself to the array of unit tests in
// the suUnitTest object (there is only a single, global
// instance of suUnitTest created). When the unit tests are run,
// the test() method of each derived object is called. An 
// example unit test function (which always passed) is show 
// below: 
//
//    UTFUNC(test)
//    {
//      VERIFY (true);      //here is test() body ...
//    }
//
// The ## is the merging operator.  a##b = ab
// The # is a stringization operator  #a = "a"

#define UTFUNC(utx)                            \
class UT##utx : public suUnitTestFunction      \
{                                              \
UT##utx ();                                    \
static UT##utx sInstance;                      \
void test ();                                  \
};                                             \
UT##utx UT##utx::sInstance;                    \
UT##utx::UT##utx () : suUnitTestFunction(#utx) \
{                                              \
  suUnitTest::gOnly().addTest(#utx,this);      \
}                                              \
void UT##utx::test ()


#define VERIFY(condition) verify (condition, #condition)
#define VERIFYFLOAT(d1,d2) verifyFloat (d1, d2)


#endif // _unittest_h_
