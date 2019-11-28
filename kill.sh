#!/bin/bash
sudo pidof python3 |xargs kill -9
gpio pwm 1 0
