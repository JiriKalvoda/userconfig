#include <wiringPi.h>
#include<string> // system()

using namespace std;
#ifdef DEB
#define D if(1)
#else
#define D if(0)
#endif

#define fo(a,b) for(int a=0;a<(b);++a)
using ll = long long;

const int pin=27;
int main()
{
	wiringPiSetup();			// Setup the library
	pinMode(pin, INPUT);		// Configure GPIO0 as an output
	pullUpDnControl(pin,PUD_UP);

	// Main program loop
	bool val=digitalRead(pin);
	while(digitalRead(pin) == val)
	{
		while(digitalRead(pin) == val)
			delay(500); 	// Delay 500ms
		delay(50); 	// Delay 500ms
	}
	system("poweroff");
	return 0;
}

