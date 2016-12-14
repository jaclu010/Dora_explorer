/*
 * steering.c
 *
 * Updated: 14/12/2016
 * Authors: Fredrik Iselius, Martin Lundberg
 */ 

#include <avr/io.h>
#include "steering.h"



void init_motors() {
	// PWM output ports
	DDRD |= (1<<DDD5);
	DDRB |= (1<<DDB4)|(1<<DDB3);
	// Rotation direction ports
	DDRA |= (1<<DDA0)|(1<<DDA1)|(1<<DDA2);
	
	/*
	 * COM0A1:0 COM0B1:= Sets the compare mode for A and B
	 * WGM02:0 Choose MAX (1) or TOP (5) as max counter value
	 * CS0 bits sets the clock source
	 * OCR0A compare value
	 * PWM settings for the wheels
	 */
	TCCR0A |= (1<<COM0A1)|(1<<COM0B1)|(1<<WGM00);
	TCCR0B |= (1<<CS01)|(1<<CS00);
	
	// PWM settings for tower motor
	TCCR1A |= (1<<COM1A1)|(1<<COM1B1)|(1<<WGM10);
	TCCR1B |= (1<<CS11)|(1<<CS10);
	
	PORTA |= (FORWARD<<LEFT)|(FORWARD<<RIGHT)|(BACKWARD<<PORTA2);	// Rotation direction wheels
}

void set_wheel_dir(uint8_t dir, uint8_t side) {
	if (dir == FORWARD) {
		if (side == BOTH) {
			PORTA |= (dir<<LEFT)|(dir<<RIGHT);
		} else {
			PORTA |= (dir<<side);
		}
	} else {
		if (side == BOTH) {
			PORTA &= (dir<<LEFT)|(dir<<RIGHT);
		} else if (side == RIGHT) {
			PORTA &= (dir<<side)|(1<<LEFT);
		} else {
			PORTA &= (dir<<side)|(1<<RIGHT);
		}
	}
}