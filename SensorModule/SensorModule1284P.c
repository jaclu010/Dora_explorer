/*
* SensorModule1284P.c
*
* Created: 11/1/2016 3:42:53 PM
*  Author: nikni459
*/
#define START_IR 0x5C
#define START_LASER 0x5D
#define START_GYRO 0x5E

#define STOP_LASER 0xFF

#define F_CPU 14745600 //external clock speed

#include <avr/io.h>
#include <util/delay.h>

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
	unsigned int baud = 15;
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
	while ( !(UCSR1A & (1<<RXC1)) )
	;
	/* Get and return received data from buffer */
	return UDR1;
}
void measure()
{	
	int num_sensors = 4;
	
	UART_Transmit(START_IR);
	_delay_us(200);
	
	for (int i = 0; i < num_sensors; i++) {
		
		unsigned int dist = 0;
		
		ADMUX &= 0xF8;
	
		switch (i)
		{
			case 1:
				ADMUX |= (1 << MUX0);
				break;
			case 2:
				ADMUX |= (1 << MUX1);
				break;
			case 3:
				ADMUX |= (1 << MUX1) | (1 << MUX0);
				break;
			case 4:
				ADMUX |= (1 << MUX2);
				break;
			case 5:
				ADMUX |= (1 << MUX2) | (1 << MUX0);
				break;
			default:
				break;
		}		
		
		//_delay_ms(7);
		
		if(ADCH > 22) //only assign distance if less than 30cm
			dist = ADCH;
		
		UART_Transmit(dist); // sends data through UART
		_delay_ms(100);
	}
	
}

void SPI_MasterInit(void)
{
	/* Set MOSI, SCK and SS as output, all others input */
	DDRB = (1<<DDB7)|(1<<DDB5)|(1<<DDB4); // pb6(MISO) should be input per default.
	/* Enable SPI, Master, set clock rate fck/16*/
	SPCR = (1<<SPE)|(1<<MSTR)|(1<<CPOL)|(1 << CPHA)|(1<<SPR1)|(1<<SPR0);
	//SPCR &= (0<<DORD); // zero - MSB, one - LSB
	//SPCR &= (0<<CPOL); // SCK low when idle
	/* Figure out CPHA. On what edge of SCK to sample data*/
}

void SPI_MasterTransmit(unsigned output)
{
	/* Start transmission */
	SPDR = output;
	
	/* Wait for transmission complete */
	while(!(SPSR & (1<<SPIF))) {
		
		
	}
}

void Simulated_Laser(void) {
	
	UART_Transmit(0x00);
	_delay_us(300);
	UART_Transmit(0x1E);
	_delay_us(300);
	for(unsigned i = 0; i < 30; i++) {
		
		if(i % 2 == 0) {
			UART_Transmit(0x01);
		}
		else {
			UART_Transmit(0x00);
		}
		_delay_us(300);
		
		UART_Transmit(i);
		
		_delay_us(300);		
		
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
	unsigned answerHigh = 0xFF;
	unsigned answerLow = 0xFF;
	
	StartSignal_Gyro();
		
	//first instruction
	unsigned output = 0x94;
	SPI_MasterTransmit(output);
	_delay_us(126);
	output = 0x00;
	SPI_MasterTransmit(output);
	_delay_us(126);
	answerHigh = SPDR;		

	SPI_MasterTransmit(output);
	_delay_us(126);
	answerLow = SPDR;		
		
	answerHigh &= 0x80;
		
	StopSignal_Gyro();
		
	if(answerHigh == 0) {
						
		StartSignal_Gyro();

		//second instruction
		output = 0x94;
		SPI_MasterTransmit(output);
		_delay_us(126);
		output = 0x00;
		SPI_MasterTransmit(output);
		_delay_us(126);
		answerHigh = SPDR;
			
		SPI_MasterTransmit(output);
		_delay_us(126);
		answerLow = SPDR;
			
		StopSignal_Gyro();
			
		answerHigh &= 0x80;
			
		if (answerHigh == 0) {									
				
			StartSignal_Gyro();

			//third instruction
			output = 0x80;
			SPI_MasterTransmit(output);
			_delay_us(126);
			output = 0x00;
			SPI_MasterTransmit(output);
			_delay_us(126);
			answerHigh = SPDR;
			SPI_MasterTransmit(output);
			_delay_us(126);
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
					_delay_us(300);
					UART_Transmit(sendHigh);
					_delay_us(300);
					UART_Transmit(sendLow);						
						
				}
					
			}										
				
		}
			
	}
}

/*
int main(void) {
	
	UART_Init();
	_delay_ms(100);
	FireFly_Init();	
	_delay_ms(100);
	AD_Init();
	_delay_ms(1000);
	
	DDRB |= (1 << DDB0);
	


	
	while(1) {
		//measure();
		UART_Transmit(START_LASER);
		_delay_us(300);
		Simulated_Laser();
		_delay_ms(1000);
		//unsigned char data = FireFly_Receive();
		//UART_Transmit(data);		
		//UART_Transmit('ö');
	}	
}
*/

int main(void)
{
	UART_Init();
	_delay_ms(100);
	FireFly_Init();
	_delay_ms(100);
	AD_Init();
	_delay_ms(100);
	SPI_MasterInit();
	_delay_ms(1000);
	DDRB |= (1 << DDB0);


	
	while(1) {
		
		Read_Gyro();
	

	}
	
			
				
}
