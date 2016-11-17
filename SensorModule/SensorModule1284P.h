#pragma once

#include <avr/io.h>
#include <util/delay.h>
#include <stdlib.h>

#define START_IR 0x5C
#define START_LASER 0x5D
#define START_GYRO 0x5E

#define NUM_SENSOR 0x06;

#define STOP_LASER 0xFF

#define F_CPU 14745600
	
typedef enum {IR_ONE, IR_TWO, IR_THREE, IR_FOUR, IR_FIVE, IR_SIX, IR_SEND} irState;
	
typedef enum {GYRO_ONE, GYRO_TWO, GYRO_THREE, GYRO_SEND} gyroState;
	
typedef enum {IR_GO, GYRO_GO, NONE} sensorState;

irState ir = IR_ONE;
gyroState gyro = GYRO_ONE;
sensorState sensor = IR_GO;

unsigned char irArray[6] = {0};
unsigned laserArray[520] = {0};
unsigned counter = 0;
unsigned sendHigh, sendLow;

