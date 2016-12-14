/*
 * uart.c
 *
 *  Updated: 14/12/2016
 *  Author: freis685
 */ 

#include <avr/io.h>
#include "uart.h"

/* Init settings for uart */
void uart_init() {
	unsigned int baud = 15;
	UBRR0 = 0;
	
	// Port 0, UART
	UCSR0A |= (1 << U2X0); // Double transmission rate
	UCSR0B |= (1 << RXEN0)|(1 << TXEN0)|(1<<RXCIE0); // Enables receive, transmit and receive interrupt
	
	UBRR0 = baud; //
}

void uart_send(unsigned data) {
	/* Wait for empty transmit buffer */
	while ( !( UCSR0A & (1<<UDRE0)) )
	;
	/* Put data into buffer, sends the data */
	UDR0 = data;
}
