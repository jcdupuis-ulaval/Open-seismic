#include <Arduino.h>
#include <ad7768.h> 
#include <command.h>
#include <stdio.h>
#include <cmath>
#include <SPI.h>
#include <Vector.h>
#include <string>

#define RS485Serial Serial3

int Mode = 9; // high = send = D2 led off, low = listen = D2 led high
command receivedCommand; 
int ODR;
int duration;
bool mustSendStatus = false;
bool mustSendData = false;
bool readyToTrig = false;
int workerStatus = IDLE;
int workerID = 2;
int chipSelectPin = 10;
ad7768_chip _default = {
		/* Configuration */
		.chipSelectPin = chipSelectPin,
		.power_mode = AD7768_ECO,
		.mclk_div = AD7768_MCLK_DIV_32,
		.dclk_div = AD7768_DCLK_DIV_8,
		.dec_rate = AD7768_DEC_X1024,
		.filt_type = AD7768_FILTER_SINC,

	};
ad7768_chip _seismic = {
		/* Configuration */
		.chipSelectPin = chipSelectPin,
		.power_mode = AD7768_ECO,
		.mclk_div = AD7768_MCLK_DIV_32,
		.dclk_div = AD7768_DCLK_DIV_8,
		.dec_rate = AD7768_DEC_X32,
		.filt_type = AD7768_FILTER_SINC,

	};
ad7768_chip configType = _default;

// pin declaration
int dout0 = 3;
int clck = 6;
int drdy = 4;


String commande;


// ISR functions
void read_ISR();
void drdy_ISR();

// binary_data-ready flags and counter
volatile bool data_packet_ready = false;
volatile int acquisition_initial_time;
volatile int data_packet_counter = 0; 


// trigger state
volatile bool init_trig_detected = false;
volatile bool triggered_state = false;

// clock count for each binary_data packet
volatile int clck_count = 0;

// binary_data buffer and precalculated 2s power
volatile int expo [32] = {0,0,0,0,0,0,0,0,pow(2,23),pow(2,22),pow(2,21),pow(2,20),
pow(2,19),pow(2,18),pow(2,17),pow(2,16),pow(2,15),pow(2,14),
pow(2,13),pow(2,12),pow(2,11),pow(2,10),pow(2,9),pow(2,8),pow(2,7),pow(2,6),pow(2,5),
pow(2,4),pow(2,3),pow(2,2),pow(2,1),pow(2,0)};
volatile int binary_data[32];
volatile double integer_data = 0;


int number_of_data_packet = 100;

// vector that holds a complete acquisition
int storage_arrayD[32000]; //TODO: This maximum array size is 1 sec for 32 khz ODR
int storage_arrayT[32000];
Vector<int> data(storage_arrayD);
Vector<int> time(storage_arrayT);


void setup() {

  RS485Serial.begin(115200);
  Serial.begin(115200);   
  pinMode(Mode,OUTPUT);
  digitalWrite(Mode,LOW);
  SPI.begin();
  pinMode(dout0, INPUT);
  pinMode(drdy, INPUT_PULLDOWN);
  pinMode(clck, INPUT);
  pinMode(chipSelectPin, OUTPUT);


  ad7768_setup(_default);
  
  

}

void loop() {

if(RS485Serial.available () >0 and readyToTrig == false) 
{
  receivedCommand = readCommand(&RS485Serial);
  if (receivedCommand.type == GLOBAL or receivedCommand.workerId == workerID)
  {
    Serial.println("called");
    Serial.println(receivedCommand.type);
    Serial.println(receivedCommand.workerId);
  if (receivedCommand.def == ARM)
  {
    workerStatus = ARMED;
    data_packet_counter = 0;
    readyToTrig = true;

    attachInterrupt(digitalPinToInterrupt(drdy), drdy_ISR, RISING);
    attachInterrupt(digitalPinToInterrupt(clck), read_ISR, FALLING);
  }
  else if (receivedCommand.def == STATUS)
  {
    digitalWrite(Mode,HIGH);
    delay(5);
    sendWorkerStatus(&RS485Serial,workerStatus,workerID);
    delay(5);
    digitalWrite(Mode,LOW);
    delay(5);
  }
  else if (receivedCommand.def == CONFIG)
   {
     Serial.print(receivedCommand.adcConfig);
     if (receivedCommand.adcConfig == DEFAULT)
     {configType = _default;}
     else if (receivedCommand.adcConfig == SEISMIC)
     {configType = _seismic;}     
     duration = receivedCommand.data.toInt();
     ad7768_setup(configType);
     workerStatus = CONFIGURED;

    delay(5);
    digitalWrite(Mode,HIGH);
    delay(5);
    sendWorkerStatus(&RS485Serial,workerStatus,workerID);
    delay(5);
    digitalWrite(Mode,LOW);

    delay(5);
    digitalWrite(Mode,HIGH);
    delay(5);
    ODR = print_config(configType, &RS485Serial);
    delay(5);
    digitalWrite(Mode,LOW);

    number_of_data_packet =  round(duration * ODR);
    Serial.println(number_of_data_packet);
    workerStatus = IDLE;
   }
  else if (receivedCommand.def == HARVEST)
  {
    mustSendData = true;
  }
  }
}
   

  if (mustSendData == true)
  {
    digitalWrite(Mode,HIGH);
     delay(5);
    RS485Serial.print(workerID);RS485Serial.println("w");
    delay(5);
    RS485Serial.print(number_of_data_packet);RS485Serial.println(':');
    delay(5);
    for (int i = 0; i < number_of_data_packet; i++)
      {
        RS485Serial.print(time.at(i));RS485Serial.print(",");RS485Serial.print(data.at(i));RS485Serial.print(':');
        delay(1);
      }
      
    digitalWrite(Mode,LOW);
    mustSendData = false;
    workerStatus = IDLE;
  }


noInterrupts();
if (readyToTrig == true and triggered_state == false)
{
 if (RS485Serial.find('t'))
{
    acquisition_initial_time = micros();
    triggered_state = true;
  }
}
if (data_packet_ready == true and triggered_state == true)
{		

    data.push_back(integer_data);
    time.push_back(micros() - acquisition_initial_time);

		data_packet_ready = false;
		data_packet_counter += 1;

		if (data_packet_counter == number_of_data_packet)
		{
      workerStatus = DATAREADY;
      // mustSendStatus = true;
			triggered_state = false;
      readyToTrig = false;
      data_packet_counter = 0;
      detachInterrupt(digitalPinToInterrupt(drdy));
      detachInterrupt(digitalPinToInterrupt(clck));
		}

}
interrupts();
}

void read_ISR() {
if (clck_count < 32){ // because the output is 32 bit long
binary_data[clck_count] = digitalRead(dout0);
clck_count += 1;


}
else if (clck_count == 33){ // directly after the last bit
	data_packet_ready = true;
	for (int i = 8; i < 32; i++) { // data bit is from 8 to 32
			integer_data +=  expo[i] * binary_data[i];
			}
	clck_count += 1;

}

else {
	clck_count += 1;
}
}

void drdy_ISR(){
	if (triggered_state == true)
	{
	clck_count = 0;
	integer_data = 0;	
	}
	

}
