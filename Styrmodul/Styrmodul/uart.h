/*
 * uart.h
 *
 *  Updated: 14/12/2016
 *  Authors: Fredrik Iselius
 */ 


#ifndef UART_H_
#define UART_H_

#define F_CPU 14745600

void uart_init();
void uart_send();
void uart_receive();

#endif /* UART_H_ */