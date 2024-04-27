import requests
import json
import os

webhook_url = 'https://oapi.dingtalk.com/robot/send?access_token=0def5a95de30fb7b22ee3a4874a8fbeb562369a96ab674e44309521da7d4d7d1'

crash_rate = 0.0
crash_rate_past = 0.0
error_rate = 0.0
error_rate_past = 0.0

# New Relic account ID和API key
NEW_RELIC_ACCOUNT_ID = 3619369
NEW_RELIC_API_KEY = os.environ["Api_Key"]

# NRQL查询
nrql_query_crash = """
query($accountId: Int!){
  actor {
    account(id: $accountId) {
      nrql(query: "SELECT percentage(uniqueCount(sessionId), where category = 'Crash') as 'Crash rate' FROM MobileSession, MobileCrash WHERE (entityGuid = 'MzYxOTM2OXxNT0JJTEV8QVBQTElDQVRJT058MTEzNDM3NDM3NQ') LIMIT 5 SINCE 259200 seconds AGO TIMESERIES") {
        results
      }
    }
  }
}
"""

nrql_query_crash_past = """
query($accountId: Int!){
  actor {
    account(id: $accountId) {
      nrql(query: "SELECT percentage(uniqueCount(sessionId), where category = 'Crash') as 'Crash rate' FROM MobileSession, MobileCrash WHERE (entityGuid = 'MzYxOTM2OXxNT0JJTEV8QVBQTElDQVRJT058MTEzNDM3NDM3NQ') LIMIT 5 SINCE 345600 seconds AGO UNTIL 86400 seconds AGO TIMESERIES") {
        results
      }
    }
  }
}
"""

nrql_query_error = """
query($accountId: Int!){
  actor {
    account(id: $accountId) {
      nrql(query: "SELECT percentage(count(*), where errorType is not null) as 'Errors and Failures Rate %' FROM MobileRequestError, MobileRequest WHERE (entityGuid = 'MzYxOTM2OXxNT0JJTEV8QVBQTElDQVRJT058MTEzNDM3NDM3NQ') LIMIT 1000 SINCE 259200 seconds AGO TIMESERIES") {
        results
      }
    }
  }
}
"""

nrql_query_error_past = """
query($accountId: Int!){
  actor {
    account(id: $accountId) {
      nrql(query: "SELECT percentage(count(*), where errorType is not null) as 'Errors and Failures Rate %' FROM MobileRequestError, MobileRequest WHERE (entityGuid = 'MzYxOTM2OXxNT0JJTEV8QVBQTElDQVRJT058MTEzNDM3NDM3NQ') LIMIT 1000 SINCE 345600 seconds AGO UNTIL 86400 seconds AGO TIMESERIES") {
        results
      }
    }
  }
}
"""

# New Relic API endpoint for NRQL queries
nrql_endpoint = f'https://api.newrelic.com/graphql'

# 请求头，包含账户ID和API key
headers = {
    'Api-Key': NEW_RELIC_API_KEY,
    'Content-Type': 'application/json'
}

# 请求体，包含NRQL查询
payload_crash = {
    'query': nrql_query_crash,
    "variables": {
        "accountId": NEW_RELIC_ACCOUNT_ID
    }
}

payload_crash_past = {
    'query': nrql_query_crash_past,
    "variables": {
        "accountId": NEW_RELIC_ACCOUNT_ID
    }
}

payload_error = {
    'query': nrql_query_error,
    "variables": {
        "accountId": NEW_RELIC_ACCOUNT_ID
    }
}

payload_error_past = {
    'query': nrql_query_error_past,
    "variables": {
        "accountId": NEW_RELIC_ACCOUNT_ID
    }
}

def get_crash_rate():
    # 发送POST请求
    response_crash = requests.post(nrql_endpoint, headers=headers, json=payload_crash)
    # 检查响应
    if response_crash.status_code == 200:
        # 请求成功，打印查询结果
        results = response_crash.json()['data']['actor']['account']['nrql']['results']
        crash_rates_sum = sum(item['Crash rate'] for item in results)
        average_crash_rate = crash_rates_sum / len(results)
        global crash_rate
        crash_rate = round(average_crash_rate, 3)
        get_crash_rate_past()
    else:
        # 请求失败，打印错误信息
        print(f'Error: {response_crash.status_code}')
        print(response_crash.text)

def get_crash_rate_past():
    # 发送POST请求
    response_crash = requests.post(nrql_endpoint, headers=headers, json=payload_crash_past)
    # 检查响应
    if response_crash.status_code == 200:
        # 请求成功，打印查询结果
        results = response_crash.json()['data']['actor']['account']['nrql']['results']
        crash_rates_sum = sum(item['Crash rate'] for item in results)
        average_crash_rate = crash_rates_sum / len(results)
        global crash_rate_past
        crash_rate_past = round(average_crash_rate, 3)
        get_error_rate()
    else:
        # 请求失败，打印错误信息
        print(f'Error: {response_crash.status_code}')
        print(response_crash.text)
def get_error_rate():
    response_error = requests.post(nrql_endpoint, headers=headers, json=payload_error)
    if response_error.status_code == 200:
        results = response_error.json()['data']['actor']['account']['nrql']['results']
        error_rates_sum = sum(item['Errors and Failures Rate %'] for item in results)
        average_error_rate = error_rates_sum / len(results)
        global error_rate
        error_rate = round(average_error_rate, 2)
        get_error_rate_past()

def get_error_rate_past():
    response_error = requests.post(nrql_endpoint, headers=headers, json=payload_error)
    if response_error.status_code == 200:
        results = response_error.json()['data']['actor']['account']['nrql']['results']
        error_rates_sum = sum(item['Errors and Failures Rate %'] for item in results)
        average_error_rate = error_rates_sum / len(results)
        global error_rate_past
        error_rate_past = round(average_error_rate, 2)
        data = {
            "msgtype": "text",
            "text": {
                "content": f"{f"Daily Monitoring: Crash Rate & Errors Rate\n\nChange compared to the previous reporting period:\n📉Crash Rate: {round((crash_rate - crash_rate_past)/crash_rate_past, 4)}bp\n🚫Errors and Failures Rate: {round((error_rate - error_rate_past)/error_rate_past, 4)}bp\n\nOver the past 3 days:\n📉Crash Rate: {crash_rate}%\n🚫Errors and Failures Rate: {error_rate}%\n\nOnward and upward! 🚀"}\n"
            },
            "at": True  # at为True时，消息中会@所有人
        }
        print(data)
        webhook_headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, headers=webhook_headers, data=json.dumps(data))
        if response.status_code == 200:
            print("消息发送成功")
        else:
            print(f"发送失败，状态码：{response.status_code}")

get_crash_rate()
