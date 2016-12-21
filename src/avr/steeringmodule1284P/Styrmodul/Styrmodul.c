/*
 * Styrmodul.c
 *
 *  Updated: 14/12/2016
 *  Author: Fredrik Iselius, Jonathan Johansson, Martin Lundberg, Niklas Nilsson
 */ 

#define F_CPU 14745600

#include <avr/io.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <stdbool.h>

#include "Styrmodul.h"
#include "uart.h"

typedef enum {LEFT_SIDE, RIGHT_SIDE, BOTH_SIDES, TOWER, NONE} sideState;

bool read_speed = false;
sideState side = NONE;

/*UART receive interrupt*/
ISR(USART0_RX_vect) {
	
	char rec_byte = UDR0;
	
	/*Sets speed 'rec_byte' to the wheel side 'side'*/
	if (read_speed) {
		switch (side) {
			case LEFT_SIDE:
				LEFT_SPEED = rec_byte;
				break;
			case RIGHT_SIDE:
				RIGHT_SPEED = rec_byte;
				break;
			case TOWER:
				LASER_SPEED = rec_byte;
				break;
			case BOTH_SIDES:
				LEFT_SPEED = rec_byte;
				RIGHT_SPEED = rec_byte;
				break;
			default:
				break;
		}	
		side = NONE;
		read_speed = false;
	} 
	/*Sets wheel direction or side*/
	else {
		switch (rec_byte) {
			case 'f':
				set_wheel_dir(FORWARD,BOTH);
				break;
			case 'b':
				set_wheel_dir(BACKWARD,BOTH);
				break;
			case 'l':
				set_wheel_dir(FORWARD,RIGHT);
				set_wheel_dir(BACKWARD,LEFT);
				break;
			case 'r':
				set_wheel_dir(FORWARD,LEFT);
				set_wheel_dir(BACKWARD,RIGHT);
				break;
			case 's':
				side = BOTH_SIDES;
				read_speed = true;
				break;
			case 'v':
				side = LEFT_SIDE;
				read_speed = true;
				break;
			case 'h':
				side = RIGHT_SIDE;
				read_speed = true;
				break;
			case 't':
				side = TOWER;
				read_speed = true;
				break;
		}
	}
}

bool hall_left_activated = false;

/*Sends 95 over uart when the left hall sensor goes low*/
ISR(PCINT2_vect) {
	if (!hall_left_activated) {
		uart_send(0x5F);
		hall_left_activated = true;
	} else {
		hall_left_activated = false;
	}
}

bool hall_right_activated = false;

/*Sends 96 over uart when the right hall sensor goes low*/
ISR(PCINT1_vect) {
	if (!hall_right_activated) {
		uart_send(0x60);
		hall_right_activated = true;
		} else {
		hall_right_activated = false;
		}
}


int main(void) {
	init_motors();
	
	LEFT_SPEED = 0; // LEFT
	RIGHT_SPEED = 0; // RIGHT
	
	LASER_SPEED = 0;
	
	DDRC &= ~(1<<DDC0);		// set pin C0 to input
	DDRB &= ~(1<<DDB1);		// set pin B1 to input
	PORTC |= (1<<PORTC0);	// activate pull-up resistor on C0
	PORTB |= (1<<PORTB1);	// activate pull-up resistor on B1
	
	PCMSK2 |= (1<<PCINT16);	// enable PCINT2
	PCICR |= (1<<PCIE2);	// activate interrupts on PCNIT23-16
	
	PCMSK1 |= (1<<PCINT9);
	PCICR |= (1<<PCIE1);
	
	EICRA |= (1<<ISC21);	// enable interrupt on falling edge
	
	uart_init();
	sei();	// enable interrupts
	
	/*Wait for interrupts*/
    while(1) {		
    }
}