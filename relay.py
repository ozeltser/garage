#!/usr/bin/env python3
import time
import os

if os.name == 'nt':
    print("This script only works on a Raspberry Pi with Automation HAT attached.")
    exit(0)

import automationhat

if automationhat.is_automation_hat():
    try:
        automationhat.light.power.write(1)
        automationhat.relay.one.on()
        time.sleep(5)
    finally:
        automationhat.relay.one.off()
        automationhat.light.power.write(0)
