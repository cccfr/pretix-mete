import requests

#meteserver = "http://172.16.0.69:3000"
meteserver = "http://mete.cloud.cccfr"
username = "schwarzelunge@cccfr.de"
userid = 0
monthly_term = 10

def get_items(category):
    items = requests.get("%s/api/v1/%s" %(meteserver, category)).json()
    return items

def get_userid():
    users = get_items("users")
    for user in users:
        if user["email"] == username:
            userid = user["id"]
            return userid

def pay_monthly_term():
    res = requests.get("%s/api/v1/users/%s/payment" %(meteserver, userid), params="amount=%s" %monthly_term)
    if res.status_code != 204:
        print("error paying for userid %s:\n%s" %(userid, res.text))
        return
    print("monthly term payed")

def main():
    global userid
    userid = get_userid()
    pay_monthly_term()


if __name__ == "__main__":
    # execute only if run as a script
    main()