import requests, json
from urllib.parse import urlencode
from time import sleep

meteserver = "http://172.16.0.69:3000"
#meteserver = "http://mete.cloud.cccfr"
pretixserver = "https://schwarzelunge.club.klaut.cloud"
organizer = "hustepeter"
username = "schwarzelunge@cccfr.de"
userid = 0
headers = {}

checked_audits = []

def filter_audits(audits):
    global checked_audits
    returns = []
    for audit in audits:
        if not audit["id"] in checked_audits:
            returns.append(audit)
            checked_audits.append(audit["id"])
    print("new payments: %s" %returns)
    return returns

def get_items(category):
    items = requests.get("%s/api/v1/%s" %(meteserver, category)).json()
    return items

def set_item(item, category):
    params = prepare_params(item, category.strip("s"))
    print(params)
    print(requests.post("%s/api/v1/%s" %(meteserver, category), params=params, headers={'Content-Type': 'application/json'}))

def del_item(id, category):
    print(requests.delete("%s/api/v1/%s/%s" %(meteserver, category, id)))

def prepare_params(item, kind):
    params = {}
    for key in item.keys():
        params[kind+"["+key+"]"] = item[key]
    return urlencode(params)

def filter_drinks(drinks):
    filterdrinks = {}
    for drink in drinks:
        #"~SL~ %s#%s~%s" %(payment.order.event.name, payment.order.code, payment.local_id)
        if "~SL~ " in drink["name"]:
            filterdrinks[drink["id"]] = {"name": drink["name"], "price": drink["price"]}
    return filterdrinks

def get_userid():
    users = get_items("users")
    for user in users:
        if user["email"] == username:
            userid = user["id"]
            return userid

def check_orders():
    # search for drinks that not have been deleted (e.g. because they are not payed) yet
    products = filter_drinks(get_items("drinks"))
    if len(products) == 0:
        return
    audits = filter_audits(get_items("audits")["audits"])
    for audit in audits:
        if audit["drink"] in products.keys():
            drinkid = audit["drink"]
            drink = products[drinkid]
            event = drink["name"].split("#")[0].split(' ')[1]
            order, payid = drink["name"].split("#")[1].split("~")
            res = requests.post("%s/api/v1/organizers/%s/events/%s/orders/%s/payments/%s/confirm/" %(pretixserver, organizer, event, order, payid), headers=headers)
            if res.status_code != 200:
                print("error confirming payment: %s" %res.text)
                continue
            res = requests.delete("%s/api/v1/drinks/%s" %(meteserver, drinkid))
            if res.status_code != 204:
                print("error deleting drink: %s" %res.text)
                continue
            res = requests.get("%s/api/v1/users/%s/deposit" %(meteserver, userid), params="amount=%s" %drink["price"])
            if res.status_code != 204:
                print("error adding deposit to userid %s:\n%s" %(userid, res.text))
                continue
            print("order %s payed" %order)

def main():
    global userid
    global headers
    with open("authHeader.json") as headerfile:
        headers = json.load(headerfile)
    userid = get_userid()
    filter_audits(get_items("audits")["audits"]) #fill cache with known payments
    while True:
        check_orders()
        sleep(3)


if __name__ == "__main__":
    # execute only if run as a script
    main()
