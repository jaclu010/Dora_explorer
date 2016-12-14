/*
 * steering.h
 *
 *  Updated: 14/12/2016
 *  Author: Fredrik Iselius, Martin Lundberg
 */ 


#ifndef STEERING_H_
#define STEERING_H_

#define F_CPU 14745600

/*PWM compare values, used to set speed*/
#define LEFT_SPEED OCR0A
#define RIGHT_SPEED OCR0B
#define LASER_SPEED OCR1A

/*PWM direction port for sides*/
#define LEFT PORTA0
#define RIGHT PORTA1

#define FORWARD 1
#define BACKWARD 0
#define BOTH 2

void init_motors();
void set_wheel_dir(uint8_t dir, uint8_t side);

#endif /* STEERING_H_ */