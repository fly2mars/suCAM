#include "timing.h"

suElapsedTime::suElapsedTime () : starting_ (0)
{
  reset ();
}


double suElapsedTime::sec () const
{
  clock_t current = clock ();
  return ((double)(current - starting_) / CLOCKS_PER_SEC);
}


void suElapsedTime::reset ()
{
  starting_ = clock ();
}


