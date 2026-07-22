// ------ ERRORS ------

// ------ VALID ------

void OnTick()
{
   int counter = 0;
   static int callCount = 0;
   const double factor = 1.5;
   double values[10];
   string names[];

   if(counter > 0)
     {
      counter = 1;
     }
   else
     {
      counter = 2;
     }

   if(counter == 1)
      counter++;
   else if(counter == 2)
      counter--;

   for(int i = 0; i < 10; i++)
     {
      values[i] = i * 2.0;
     }

   while(counter < 10)
     {
      counter += 1;
     }

   do
     {
      counter -= 1;
     }
   while(counter > 0);

   do counter++; while(counter < 3);

   switch(counter)
     {
      case 0:
         counter = 5;
         break;
      case 1:
      case 2:
         counter = 6;
         break;
      default:
         counter = -1;
         break;
     }

   int mode = counter > 0 ? 1 : 0;
   counter = mode == 1 ? counter + 1 : counter - 1;

   string message = "done";
   Print(message);
   PlaySound("alert.wav");
   ;

   if(counter > 100)
      return;

   {
      int nested = 1;
      nested++;
   }
}

int Add(int a, int b)
{
   int sum = a + b;
   return sum;
}

double Ratio(double x)
{
   if(x == 0.0)
      return 0.0;
   return (1.0 / x);
}
