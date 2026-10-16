import time
from twelvedata import TDClient
import os
messages_history = []

def on_event(event):
    print(event) # prints out the data record (dictionary)
    messages_history.append(event)

td = TDClient(apikey=os.getenv("TWELVEDATA_API_KEY"))
ws = td.websocket(symbols=["BTC/USD", "ETH/USD"], on_event=on_event)
ws.subscribe(['ETH/BTC', 'AAPL'])
ws.connect()
while True:
    print('messages received: ', len(messages_history))
    ws.heartbeat()
    time.sleep(10)