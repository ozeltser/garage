#!/usr/bin/env python3
import sys
import automationhat

# First, check if the Automation HAT is connected to the Raspberry Pi.
try:
    if automationhat.is_automation_hat():
        try:
            input_one_state = automationhat.input.one.read()
            if input_one_state > 0:
                print("Door Closed")
            else:
                print("Door Opened")
        except Exception as e:
            print(f'Failed to read door sensor input: {e}', file=sys.stderr)
    else:
        print('Automation HAT not found.', file=sys.stderr)
except Exception as e:
    print(f'Automation HAT not found: {e}', file=sys.stderr)
