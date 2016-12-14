/*
 * SensorModule1284P.c
 *
 * Updated: 29/11/2016
 * Author: Fredrik Iselius, Jacob Lundberg, Niklas Nilsson
 */ 

#pragma once

/* Define the clock speed */
#define F_CPU 14745600

#include <avr/io.h>
#include <util/delay.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

/* Start ID bytes */
#define START_IR 0x5C
#define START_LASER 0x5D
#define START_GYRO 0x5E

/* Number of IR sensors */
#define NUM_SENSOR 0x06;

/* STOP ID byte */
#define STOP_LASER 0xFF

typedef enum {IR_ONE, IR_TWO, IR_THREE, IR_FOUR, IR_FIVE, IR_SIX, IR_SEND} irState;	
typedef enum {GYRO_ONE, GYRO_TWO, GYRO_SEND, GYRO_INIT} gyroState;	
typedef enum {IR_GO, GYRO_GO, NONE} sensorState;

irState ir = IR_ONE;
gyroState gyro = GYRO_INIT;
sensorState sensor = IR_GO;

unsigned char irArray[6] = {0};
unsigned laserArray[520] = {0};
unsigned counter = 0;
unsigned sendHigh, sendLow;