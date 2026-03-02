import requests
import json

headers = {"accept": "application/json"}
url = "https://api.coingecko.com/api/v3/coins/bitcoin"
params = {
    "localization": "false",
    "tickers": "false",
    "market_data": "true",
    "community_data": "false",
    "developer_data": "false"
}
try:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print("BTC status:", response.status_code)
    result = response.json()
    if 'market_data' in result:
        print("BTC market_data is present")
        print("Price:", result['market_data']['current_price']['usd'])
        print("Market Cap:", result['market_data']['market_cap']['usd'])
    else:
        print("No market_data:", list(result.keys()))
except Exception as e:
    print("Error:", e)

url2 = "https://api.coingecko.com/api/v3/global"
try:
    response2 = requests.get(url2, headers=headers, timeout=30)
    print("Global status:", response2.status_code)
    result2 = response2.json()
    if 'data' in result2 and 'total_market_cap' in result2['data']:
        print("Global total_market_cap is present")
        print("Total MC:", result2['data']['total_market_cap']['usd'])
    else:
        print("No total_market_cap:", list(result2.keys()))
except Exception as e:
    print("Error:", e)
