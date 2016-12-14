/*
 * LaserModule2313.h
 *
 * Updated: 1/12/2016
 * Author: Jacob Lundberg, Niklas Nilsson
 */ 

#pragma once

/* Define the clock speed */
#define F_CPU 14745600UL

#include <avr/io.h>
#include <util/delay.h>
#include "i2cmaster.h" // i2c library

/* Delay value for free running mode */
#define LASER_SPEED 0x01

/* Start ID byte */
#define START_LASER 0x5D

/* Lidar Lite v3 i2c address */
#define LASER 0xC4

typedef enum {STATE_RUNNING, STATE_HALL} state;
	
typedef enum {FREE_RUNNING, BUSY_WAITING} mode;
	
unsigned counter = 0;
unsigned counterHigh = 0;
state state_ = STATE_RUNNING;

mode mode_ = BUSY_WAITING;

