import json,urllib.request,urllib.error,time,sys
B="https://api.elections.kalshi.com/trade-api/v2"
def get(p,tries=10):
    for i in range(tries):
        try: return json.load(urllib.request.urlopen(B+p,timeout=25))
        except urllib.error.HTTPError as e:
            time.sleep(4*(i+1))
        except Exception: time.sleep(3)
