/*
 * SensorModule1284P.c
 *
 * Updated: 01/12/2016
 * Author: Fredrik Iselius, Jacob Lundberg, Niklas Nilsson
 */ 

#include "SensorModule1284P.h"

void AD_Init()
{
	DDRA = 0b00000000;
	
	ADCSRA |= (1 << ADPS2); // sets the ADC prescalar
	
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
		
	UBRR0 = baud; // sets baud rate
}

void SPI_MasterInit()
{
	/* Set MOSI, SCK and SS as output, all others input */
	DDRB = (1<<DDB7)|(1<<DDB5)|(1<<DDB4); // pb6(MISO) should be input per default.
	
	/* Enable SPI, Master, set clock rate */
	SPCR = 0b01011101;
	
}

void FireFly_Init() {
	unsigned int baud = 15; 
	UBRR1 = 0;
	
	// Port 1, FireFly
	UCSR1A |= (1 << U2X1);
	UCSR1B |= (1 << RXEN1) | (1 << TXEN1); // enables rx and tx	

	UBRR1 = baud; // sets baud rate
}

void UART_Transmit(unsigned data) {
	/* Wait for empty transmit buffer */
	while ( !( UCSR0A & (1<<UDRE0)) )
	;
	/* Put data into buffer, sends the data */
	UDR0 = data;
}

void SPI_MasterTransmit(unsigned output)
{
	/* Start transmission */
	SPDR = output;
	
	/* Wait for transmission complete */
	while(!(SPSR & (1<<SPIF))) {
		
		
	}
}

void FireFly_Transmit(unsigned data) {
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
/* Sends IR values in cm over UART */
void Send_IR() {	
	
	UART_Transmit(START_IR);
	UART_Transmit(irArray[0]);
	UART_Transmit(irArray[1]);
	UART_Transmit(irArray[2]);
	UART_Transmit(irArray[3]);
	UART_Transmit(irArray[4]);
	UART_Transmit(irArray[5]);
	
	sensor = GYRO_GO; // set sensor state to gyro
	
}

/* Iterate through sensors and save readings */
void Read_IR() {
	
	
	if(ir != IR_SEND) {
		
		unsigned AD_VALUE = ADCH;
		
		if(AD_VALUE > 22)
			irArray[ir] = round((-4.935*AD_VALUE + 804.5) / (AD_VALUE + 9.051)); //convert sensor data to cm		
		else
			irArray[ir] = 25; // if invalid ir value set distance to 25cm
			
	}
	
	ADMUX &= 0xF8; // reset ADMUX
	
	switch (ir)
	{
		case IR_ONE:
			ADMUX |= (1 << MUX0); // set ADMUX to read the next sensor
			ir = IR_TWO; // go to next state
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

/* Pull SS low */
void StartSignal_Gyro() {
	
	PORTB &= (0 << PORTB4);
	
}

/* Pull SS high */
void StopSignal_Gyro() {
	
	PORTB |= (1 << PORTB4);
	
}

/* Starts Gyro conversation and saves the result */
void Read_Gyro()
{
	
	unsigned output;
	unsigned answerHigh;
	unsigned answerLow;
	
	switch(gyro) {		
		
		case GYRO_ONE: // Start a reading

			StartSignal_Gyro();

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
				gyro = GYRO_TWO;
	
		break;
		
		case GYRO_TWO: // Get and save the result
		
			StartSignal_Gyro();
			
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
		
		case GYRO_SEND: // Send the result over UART

			UART_Transmit(START_GYRO);
			UART_Transmit(sendHigh);
			UART_Transmit(sendLow);
			
			gyro = GYRO_ONE;
			sensor = IR_GO;
		break;
		
		case GYRO_INIT: // Turn the Gyro on		
			output = 0x94;
			SPI_MasterTransmit(output);
			
			output = 0x00;
			SPI_MasterTransmit(output);
			answerHigh = SPDR;

			SPI_MasterTransmit(output);
			answerLow = SPDR;
			
			StopSignal_Gyro();
			
			UART_Transmit(0xFE);
			
			gyro = GYRO_ONE;
		break;		
		default:
		break;
		
	}
	
}

void Sync_Laser()
{
		unsigned char sync = 0x00;
		while (1){
			
			sync = FireFly_Receive();
			
			if (sync == START_LASER)				
				break;
			
		}
}

/* Receive laser reading via bluetooth and transmit it over UART */
void Read_Laser() {

	Sync_Laser(); // wait for start id byte to be sent
		
	
	unsigned char high = FireFly_Receive();
	
	UART_Transmit(START_LASER);
	UART_Transmit(high);
	
	if(high == 0xFF) { // if stop byte is received, send it and number of laser readings
		
		unsigned highCounter = FireFly_Receive();
		unsigned lowCounter = FireFly_Receive();		

		unsigned laserCounter = (highCounter << 8);
		laserCounter |= lowCounter;
		
		UART_Transmit(abs(laserCounter-counter));
		UART_Transmit(highCounter);
		UART_Transmit(lowCounter);
		
		counter = 0;
		sensor = NONE; // disable ir or gyro sensor reading for next loop to avoid missing first laser value
		
	}
	else {
		
		unsigned char low = FireFly_Receive();
	
		UART_Transmit(low);
		counter++;
		if(sensor == NONE){ // enable ir sensor reading after first value is received
			sensor = IR_GO;
			ir = IR_ONE;
		}
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
	
	
	while(1) {		
		
		Read_Laser();
		
		if(sensor == GYRO_GO)
			Read_Gyro();
		if(sensor == IR_GO)
			Read_IR();


	}			
				
}
