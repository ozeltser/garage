#!/usr/bin/env python3
import time
import automationhat

if automationhat.is_automation_hat():
    try:
        automationhat.light.power.write(1)
        automationhat.relay.one.on()
        time.sleep(5)
    finally:
        automationhat.relay.one.off()
        automationhat.light.power.write(0)
