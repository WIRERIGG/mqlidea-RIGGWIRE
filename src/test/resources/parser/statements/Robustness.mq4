// Weird / incomplete statements: the tolerant statement parser must not report
// parse errors here — unrecognized content falls back to plain token consumption.

// ------ ERRORS ------

// ------ VALID ------

void Strange()
{
   this is not a statement
   another line without semicolon
   if without parens
   do nothing
   x = = 5;
   switch(x) y = 1;
   + - * /
   return
}

int AfterRecovery()
{
   return 42;
}
