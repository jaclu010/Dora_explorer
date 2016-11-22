/*
 * LaserModule2313.c
 *
 * Created: 11/3/2016 2:03:10 PM
 *  Author: nikni459
 */ 

#include "LaserModule2313.h"

void FireFly_Init() 
{
	unsigned int baud = 15;
	UBRRH = 0;
	
	// Port 1, FireFly
	UCSRA |= (1 << U2X);
	UCSRB |= (1 << RXEN) | (1 << TXEN); // enables rx and tx
	
	UBRRL = baud;
}

void FireFly_Transmit(unsigned int data) 
{
	/* Wait for empty transmit buffer */
	while ( !( UCSRA & (1<<UDRE)) )
	;
	/* Put data into buffer, sends the data */
	UDR = data;
}

void Initiate_Measurement()
{
	i2c_start_wait(LASER+I2C_WRITE);
	i2c_write(0x00);
	i2c_write(0x04);
	i2c_stop();
}


void LIDAR_Init(){
	
	/* Send Start ack test */
	i2c_start(LASER+I2C_WRITE);
	
	if(mode_ == BUSY_WAITING) {
		
		/* Set mode to higher speed when lower range */
		i2c_start_wait(LASER+I2C_WRITE);
		i2c_write(0x04);
		i2c_write(0x00);
		i2c_stop();
				
		/* Set mode to high speed but short range */
		i2c_start_wait(LASER+I2C_WRITE);
		i2c_write(0x02);
		i2c_write(0x1d);
		i2c_stop();		
		
	}
	
	else {
		
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
		
	}
	/* Initiate measurement */
	Initiate_Measurement();
}

void Busy_Wait()
{

	unsigned i = 1;
	do {
		i2c_start_wait(LASER+I2C_WRITE);
		i2c_write(0x01);
		i2c_stop();
		
		i2c_start_wait(LASER+I2C_READ);
		i = i2c_readNak();
		i2c_stop();
		i &= 0x01;
	} while (i == 1);	

}




int main(void) {
	
	DDRB |= (1 << DDB1);
	
	FireFly_Init();
	i2c_init();

	_delay_ms(3000);	
	
	LIDAR_Init();
	
    while(1)
    {		
		
		if(mode_ == FREE_RUNNING)
			_delay_ms(2);
		else
			Busy_Wait();			
			
		i2c_start_wait(LASER+I2C_WRITE);
        i2c_write(0x8f);
		i2c_stop();
		
		i2c_start_wait(LASER+I2C_READ);	
		unsigned first = i2c_readAck();
		unsigned second = i2c_readNak();
		i2c_stop();
		
		if(mode_ == BUSY_WAITING)
			Initiate_Measurement();
			
		FireFly_Transmit(START_LASER);
        FireFly_Transmit(first);
		FireFly_Transmit(second);		

		counter++;

		/* Sense Hall Sensor */ 
		if (!(PIND & 0b00001000) && (state_ == STATE_RUNNING)){
			state_ = STATE_HALL;
			PORTB |= (1 << PORTB1);
			prevHigh |= (counter >> 8);
			FireFly_Transmit(START_LASER);
			FireFly_Transmit(0xFF);
			FireFly_Transmit(prevHigh);
			FireFly_Transmit(counter);
			
			counter = 0;
			prevHigh = 0;
		} else if ((PIND & 0b00001000) && (state_ == STATE_HALL))  {
			state_ = STATE_RUNNING;
			PORTB &= (0 << PORTB1);
		}
    }
}