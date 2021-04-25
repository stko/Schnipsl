import requests
import json
import sys

def main():
    if len(sys.argv)>2:
        url = 'http://'+sys.argv[2]+':8080/jsonrpc'
    else:
        url = "http://192.168.1.79:8080/jsonrpc"
    if len(sys.argv)>3:
        player_id = int(sys.argv[3])
    else:
        player_id = 1
    #url = "http://kodiwohnzimmer.fritz.box:8080/jsonrpc"
    #url = "http://kodi-wohnzimmer.fritz.box:8080/jsonrpc"
    #url = "http://192.168.2.30:8080/jsonrpc"
    #url = "http://192.168.1.94:8080/jsonrpc"

    # Example echo method
    payload ={"jsonrpc":"2.0", "id" : player_id, "method": "Player.Open", "params":{"item":{"file":sys.argv[1]}}}
    
    response = requests.post(url, json=payload).json()

    print(url, repr(payload))
    print(response)

if __name__ == "__main__":
    main()
