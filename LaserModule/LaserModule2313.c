/*
 * LaserModule2313.c
 *
 * Created: 11/3/2016 2:03:10 PM
 *  Author: nikni459
 */ 

#define F_CPU 14745600
#define LASER_SPEED 0x04
#include <avr/io.h>
#include <util/delay.h>
#include "i2cmaster.h"

//#include "USI_TWI_Master.h"

#define LASER 0xC4

void FireFly_Init() {
	unsigned int baud = 15;
	UBRRH = 0;
	
	// Port 1, FireFly
	UCSRA |= (1 << U2X);
	UCSRB |= (1 << RXEN) | (1 << TXEN); // enables rx and tx
	
	UBRRL = baud;

}

void FireFly_Transmit(unsigned int data) {
	/* Wait for empty transmit buffer */
	while ( !( UCSRA & (1<<UDRE)) )
	;
	/* Put data into buffer, sends the data */
	UDR = data;
}

unsigned char FireFly_Recieve()
{
	/* Wait for data to be received */
	while ( !(UCSRA & (1<<RXC)) )
	;
	/* Get and return received data from buffer */
	return UDR;
}

void LIDAR_Init()
{
		/* Send Start ack test */
	unsigned acc = i2c_start(LASER+I2C_WRITE);
		
	/* Set Free Running Mode */
	i2c_write(0x11);                   
	i2c_write(0xFF);
	i2c_stop();
	
	/* Set use "MEASURE_DELAY" */
	i2c_start_wait(LASER+I2C_WRITE);
	i2c_write(0x04);
	i2c_write(0x28);
	i2c_stop();
	
	/* Set new Free Running delay */
	i2c_start_wait(LASER+I2C_WRITE);
	i2c_write(0x45);
	i2c_write(LASER_SPEED);		// <- Actual delay
	i2c_stop();
				
	/* Initiate measurements */
	i2c_start_wait(LASER+I2C_WRITE);                      
	i2c_write(0x00);                       
	i2c_write(0x04);
	i2c_stop();                            
			
}

/*
void I2C_Send() {
	unsigned char i2c_buffer[6] = {0};
	
	i2c_buffer[0] = 0xC4;
	i2c_buffer[1] = 0x00;
	i2c_buffer[2] = 0x04;
	USI_TWI_Start_Transceiver_With_Data(i2c_buffer, 3);
	
	/*unsigned int i = 1;
	do {
		
		i2c_buffer[0] = 0xC5;
		i2c_buffer[1] = 0x01;
		USI_TWI_Start_Transceiver_With_Data(i2c_buffer, 3);
		i2c_buffer[2] &= 0x01;
		i = i2c_buffer[2];
		FireFly_Transmit('a');
	} while(i == 1);

	_delay_ms(2);
	i2c_buffer[0] = 0xC4;
	i2c_buffer[1] = 0x10;
	USI_TWI_Start_Transceiver_With_Data(i2c_buffer, 2);
	
	_delay_ms(1);
	i2c_buffer[0] = 0xC5;
	USI_TWI_Start_Transceiver_With_Data(i2c_buffer, 3);	
	FireFly_Transmit(i2c_buffer[2]);
}*/
	
int main(void) {
	
	DDRD |= (1 << DDD4) | (1 << DDD6);
	
	
	PORTD |= (1 << PORTD6);
	
	
	FireFly_Init();
	_delay_ms(1000);
	
	//USI_TWI_Master_Initialise();
	i2c_init();
	
	
	_delay_ms(1000);
	
	
	unsigned dist;
	unsigned read1;
	unsigned read2;
	
	LIDAR_Init();

			
	_delay_ms(2);

    while(1)
    {
		int i = 0;
		/* Busy waiting loop */
		/*
		unsigned i = 1;
		do {		
		i2c_start_wait(LASER+I2C_WRITE);
		i2c_write(0x01);
		i2c_stop();
		
		i2c_start_wait(LASER+I2C_READ);
		i = i2c_readNak();
		i &= 0x01;
		} while (i == 1); */
		
		i2c_start_wait(LASER+I2C_WRITE);
        i2c_write(0x8f);
		i2c_stop();
		
		i2c_start_wait(LASER+I2C_READ);
        FireFly_Transmit(i2c_readAck());
		_delay_us(333);
		FireFly_Transmit(i2c_readNak());
		_delay_us(333);
		i2c_stop();
		FireFly_Transmit('ö');
		_delay_us(333);
		
		/*read1 = i2c_readAck();                  
		read2 = i2c_readNak();
        i2c_stop();                    
		
		FireFly_Transmit(read1);
		_delay_us(200);
		FireFly_Transmit(read2);
		_delay_us(200);
		FireFly_Transmit('ö');
		_delay_us(200);*/
		
    //}
		
		

    }
}