#pragma once

// \file timing.h
//
#include <time.h>

/*\class suElapsedTime
\biref Elapsed time computation.
*/

class suElapsedTime
{
public:
  suElapsedTime ();
  // Record the current time

  double msec () const { return sec() * 1000;}
  double sec  () const;
  // Return elapsed time, in milliseconds or sec

  void reset ();
  // Reset the current time

private:
  clock_t starting_;  // Starting time
};

