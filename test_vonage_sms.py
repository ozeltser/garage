import os
from vonage import Auth, Vonage
from vonage_sms import SmsMessage # <-- Make sure you have this import

auth = Auth(api_key="b3d221ba", api_secret="ciIb51igUOYHr8Gg")

# if you want to manage your secret, please do so by visiting your API Settings page in your dashboard
client = Vonage(auth=auth)


message = SmsMessage(
    to="19175759619",
    from_="16628265504",
    text="Hello from Vonage!"
)

responseData = client.sms.send(message)


if responseData.messages[0].status == "0":
    print("Message sent successfully!")
    # You can also access other properties this way:
    print(f"Message ID: {responseData.messages[0].message_id}")
else:
    # Access the error text
    print(f"Message failed with error: {responseData.messages[0].error_text}")
