#pragma once

#define F_CPU 14745600

#include <avr/io.h>
#include <util/delay.h>
#include "i2cmaster.h"

#define LASER_SPEED 0x01
#define START_LASER 0x5D
#define LASER 0xC4

typedef enum {STATE_RUNNING, STATE_HALL} state;
	
typedef enum {FREE_RUNNING, BUSY_WAITING} mode;
	
unsigned counter = 0;
unsigned prevHigh = 0;

state state_ = STATE_RUNNING;

mode mode_ = BUSY_WAITING;

