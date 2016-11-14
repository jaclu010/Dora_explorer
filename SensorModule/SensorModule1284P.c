/*
* SensorModule1284P.c
*
* Created: 11/1/2016 3:42:53 PM
*  Author: nikni459
*/
#define START_IR 0x5C
#define START_LASER 0x5D
#define START_GYRO 0x5E
#define NUM_SENSOR 0x06;

#define STOP_LASER 0xFF

#define F_CPU 14745600 //external clock speed

#include <avr/io.h>
#include <util/delay.h>
#include <stdlib.h>

unsigned laserArray[520] = {0};
unsigned counter = 0;

unsigned sendHigh, sendLow;


unsigned char previous = 0x00;

typedef enum {LASER_RUNNING, LASER_SYNCING} state;
	
typedef enum {IR_ONE, IR_TWO, IR_THREE, IR_FOUR, IR_FIVE, IR_SIX, IR_SEND} irState;
	
typedef enum {GYRO_ONE, GYRO_TWO, GYRO_THREE, GYRO_SEND} gyroState;
	
typedef enum {IR_GO, GYRO_GO, SENSOR_GO} sensorState;


state state_ = LASER_SYNCING;

irState ir = IR_ONE;

gyroState gyro = GYRO_ONE;

sensorState sensor = IR_GO;

unsigned char irArray[6] = {0};


void AD_Init()
{
	DDRA = 0b00000000;
	
	ADCSRA |= (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0); // sets the ADC prescalar to 128
	
	ADMUX |= (1 << REFS0); // sets the ref voltage to ADCC(pin 30)
	ADMUX &= 0xF8; // clears MUX1-3 bits(these determines which ADC channel is used)
	
	ADCSRA |= (1 << ADATE); // enables mode choosing
	ADCSRB &= 0xF8; // sets mode to Free Running
	
	ADMUX |= (1 << ADLAR); // sets the adc to write 8 highest bits to the ADCH register
	
	ADCSRA |= (1 << ADEN); // enables the adc
	
	ADCSRA |= (1 << ADSC); // starts measuring
}

void UART_Init() {
	unsigned baud = 7;
	UBRR0 = 0;
	
	// Port 0, UART
	UCSR0A |= (1 << U2X0);
	UCSR0B |= (1 << RXEN0) | (1 << TXEN0); // enables rx and tx
		
	UBRR0 = baud; //
}

void FireFly_Init() {
	unsigned int baud = 15;
	UBRR1 = 0;
	
	// Port 1, FireFly
	UCSR1A |= (1 << U2X1);
	UCSR1B |= (1 << RXEN1) | (1 << TXEN1); // enables rx and tx	

	UBRR1 = baud;
}

void UART_Transmit(unsigned int data) {
	/* Wait for empty transmit buffer */
	while ( !( UCSR0A & (1<<UDRE0)) )
	;
	/* Put data into buffer, sends the data */
	UDR0 = data;
}

void FireFly_Transmit(unsigned int data) {
	/* Wait for empty transmit buffer */
	while ( !( UCSR1A & (1<<UDRE1)) )
	;
	/* Put data into buffer, sends the data */
	UDR1 = data;
	
}

unsigned char FireFly_Receive()
{

	/* Wait for data to be received */
	while ( !(UCSR1A & (1<<RXC1)) );
	
	/* Get and return received data from buffer */
	return UDR1;
}

void Send_IR() {
	
	UART_Transmit(START_IR);
	UART_Transmit(irArray[0]);
	UART_Transmit(irArray[1]);
	UART_Transmit(irArray[2]);
	UART_Transmit(irArray[3]);
	UART_Transmit(irArray[4]);
	UART_Transmit(irArray[5]);
	
	//sensor = GYRO_GO;
	
}

void Read_IR() {
	
	if(ir != IR_SEND) {
		if(ADCH > 22)
			irArray[ir] = ADCH;
		else
			irArray[ir] = 0;
	}
	
	ADMUX &= 0xF8;
	switch (ir)
	{
		case IR_ONE:
			ADMUX |= (1 << MUX0); // sets the mux for the next read
			ir = IR_TWO; // sets the next state
		break;
		case IR_TWO:
			ADMUX |= (1 << MUX1);
			ir = IR_THREE;
		break;
		
		case IR_THREE:
			ADMUX |= (1 << MUX1) | (1 << MUX0);
			ir = IR_FOUR;
		break;
		
		case IR_FOUR:
			ADMUX |= (1 << MUX2);
			ir = IR_FIVE;
		break;
		
		case IR_FIVE:
			ADMUX |= (1 << MUX2) | (1 << MUX0);
			ir = IR_SIX;
		break;
		
		case IR_SIX:
			ir = IR_SEND;
		break;
		
		case IR_SEND:
			Send_IR();
			ir = IR_ONE;
		break;
		default:
		break;
		
	}
	
	
}

void SPI_MasterInit(void)
{
	/* Set MOSI, SCK and SS as output, all others input */
	DDRB = (1<<DDB7)|(1<<DDB5)|(1<<DDB4); // pb6(MISO) should be input per default.
	/* Enable SPI, Master, set clock rate fck/16*/
	SPCR = (1<<SPE)|(1<<MSTR)|(1<<CPOL)|(1 << CPHA)|(1<<SPR1)|(1<<SPR0);
	
}

void SPI_MasterTransmit(unsigned output)
{
	/* Start transmission */
	SPDR = output;
	
	/* Wait for transmission complete */
	while(!(SPSR & (1<<SPIF))) {
		
		
	}
}

void StartSignal_Gyro(void) {
	
	PORTB &= (0 << PORTB4);
	
}

void StopSignal_Gyro(void) {
	
	PORTB |= (1 << PORTB4);
	
}

void Read_Gyro()
{
	
	unsigned output;
	unsigned answerHigh;
	unsigned answerLow;
	
	switch(gyro) {
		
		case GYRO_ONE:
			//first instruction
			output = 0x94;
			SPI_MasterTransmit(output);
			
			output = 0x00;
			SPI_MasterTransmit(output);
			answerHigh = SPDR;

			SPI_MasterTransmit(output);
			answerLow = SPDR;
			
			answerHigh &= 0x80;
			
			StopSignal_Gyro();
			
			if(answerHigh == 0)
				gyro = GYRO_TWO;
		
		break;
		
		case GYRO_TWO:

			StartSignal_Gyro();

			//second instruction
			output = 0x94;
			SPI_MasterTransmit(output);
			
			output = 0x00;			
			SPI_MasterTransmit(output);
			answerHigh = SPDR;
				
			SPI_MasterTransmit(output);
			answerLow = SPDR;
			
			StopSignal_Gyro();
				
			answerHigh &= 0x80;
			
			if(answerHigh == 0)
				gyro = GYRO_THREE;
			else
				gyro = GYRO_ONE;
		
		break;
		
		case GYRO_THREE:
		
			StartSignal_Gyro();

			//third instruction
			output = 0x80;
			SPI_MasterTransmit(output);
			
			output = 0x00;			
			SPI_MasterTransmit(output);
			answerHigh = SPDR;
			
			SPI_MasterTransmit(output);
			answerLow = SPDR;
			
			StopSignal_Gyro();

			unsigned checkEOC = answerHigh & 0x20;
			unsigned checkAcc = answerHigh & 0x80;
			
			if (checkEOC == 0x20) {
							
				if(checkAcc == 0) {
					
					sendLow = answerHigh & 0x01;
					sendLow = (answerHigh << 7);
					unsigned temp = (answerLow >> 1);
					temp &= 0x7F;
					sendLow = sendLow | temp;
					sendHigh = (answerHigh >> 1);
					sendHigh &= 0x07;
					
					gyro = GYRO_SEND;
				}
				
				else
					gyro = GYRO_ONE;
			}
			
			else
				gyro = GYRO_ONE;
		
		break;
		
		case GYRO_SEND:
			UART_Transmit(START_GYRO);
			UART_Transmit(sendHigh);
			UART_Transmit(sendLow);
			
			sensor = IR_GO;
			gyro = GYRO_ONE;
		break;
		
		default:
		break;
		
	}
	
}

/*
void Read_Gyro()
{
	unsigned answerHigh = 0xFF;
	unsigned answerLow = 0xFF;
	
	StartSignal_Gyro();
	
	//first instruction
	unsigned output = 0x94;
	SPI_MasterTransmit(output);
	output = 0x00;
	SPI_MasterTransmit(output);
	answerHigh = SPDR;

	SPI_MasterTransmit(output);
	answerLow = SPDR;
	
	answerHigh &= 0x80;
	
	StopSignal_Gyro();
	
	if(answerHigh == 0) {
		
		StartSignal_Gyro();

		//second instruction
		output = 0x94;
		SPI_MasterTransmit(output);
		output = 0x00;
		SPI_MasterTransmit(output);
		answerHigh = SPDR;
		
		SPI_MasterTransmit(output);
		answerLow = SPDR;
		
		StopSignal_Gyro();
		
		answerHigh &= 0x80;
		
		if (answerHigh == 0) {
			
			StartSignal_Gyro();

			//third instruction
			output = 0x80;
			SPI_MasterTransmit(output);
			output = 0x00;
			SPI_MasterTransmit(output);
			answerHigh = SPDR;
			SPI_MasterTransmit(output);
			answerLow = SPDR;
			StopSignal_Gyro();

			unsigned checkEOC = answerHigh & 0x20;
			unsigned checkAcc = answerHigh & 0x80;
			
			if (checkEOC == 0x20) {
				
				if(checkAcc == 0) {
					
					answerHigh &= 0x0F;
					
					unsigned sendLow = answerHigh & 0x01;
					sendLow = (answerHigh << 7);
					unsigned test = (answerLow >> 1);
					test &= 0x7F;
					sendLow = sendLow | test;
					unsigned sendHigh = (answerHigh >> 1);
					
					UART_Transmit(START_GYRO);
					_delay_us(30);
					UART_Transmit(sendHigh);
					_delay_us(30);
					UART_Transmit(sendLow);
					
				}
				
			}
			
		}
		
	}
}*/

void Read_Laser() {

	unsigned char test = 0x00;
		while (1){
			
			test = FireFly_Receive();
			if (test == START_LASER){				
				break;
			}
			
		}		
	
	unsigned char high = FireFly_Receive();
	
	UART_Transmit(START_LASER);
	UART_Transmit(high);
		
	if(high == 0xFF) {
		
		unsigned highCounter = FireFly_Receive();
		unsigned lowCounter = FireFly_Receive();		

		unsigned laserCounter = (highCounter << 8);
		laserCounter |= lowCounter;
		
		//felhantering för overflow av pruttar
		UART_Transmit(abs(laserCounter-counter));
		UART_Transmit(highCounter);
		UART_Transmit(lowCounter);
		
		counter = 0;
		sensor = SENSOR_GO;
		
	}
	else {
		
		unsigned char low = FireFly_Receive();
	
		UART_Transmit(low);
		counter++;
		if(sensor == SENSOR_GO)
			sensor = GYRO_GO;
	}

}


int main(void)
{
	UART_Init();
	_delay_ms(100);
	FireFly_Init();
	_delay_ms(100);
	AD_Init();
	_delay_ms(100);
	SPI_MasterInit();
	DDRB |= (1 << DDB0);
	
	
	while(1) {		
		
		//Read_Laser();
		
		if(sensor == IR_GO)
			Read_IR();			
		
		if(sensor == GYRO_GO)
			Read_Gyro();


	}			
				
}
