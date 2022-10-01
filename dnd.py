import requests
import json

URL_ITEM = 'https://character-service.dndbeyond.com/character/v5/inventory/item'
URL_CUSTOM = 'https://character-service.dndbeyond.com/character/v5/custom/value'
URL_CHARACTER = 'https://character-service.dndbeyond.com/character/v5/character/'
URL_AUTH = 'https://auth-service.dndbeyond.com/v1/cobalt-token'
URL_TRANSACTION = 'https://character-service.dndbeyond.com/character/v5/inventory/currency/transaction'

f = open('session.txt')
COBALT_SESSION = f.read()
print(COBALT_SESSION)
f.close()



'''
With COBALT_SESSION set to a valid session ID, this will return an auth token for DND Beyond. Unknown how long this token lasts for.
'''
def get_auth():
    headers = {
        'Accept': '*/*'
    }
    cookies = {"CobaltSession": COBALT_SESSION}

    res = requests.post(URL_AUTH, headers=headers, cookies=cookies)
    return res.json()['token']

def add_item(characterId, entityId, entityTypeId, quantity):
    containerEntityTypeId = 1581111423 # This is for the equipment section of inventory
    headers = {
        'Accept': '*/*', 
        'Content-Type': 'application/json;charset=utf-8', 
        'Authorization': 'Bearer ' + get_auth()
    }

    data = {
        'characterId' : characterId,
        'equipment' : [
            {
                'containerEntityId' : characterId, # characterId for equipment section of inventory
                'containerEntityTypeId' : containerEntityTypeId,
                'entityId' : entityId,
                'entityTypeId' : entityTypeId,
                'quantity' : quantity
            }
        ]
    }

    data = json.dumps(data)
    res = requests.post(URL_ITEM, data=data, headers=headers)
    return res.json()

def delete_item(characterId, id):
    headers = {
        'Accept': '*/*', 
        'Content-Type': 'application/json;charset=utf-8', 
        'Authorization': 'Bearer ' + get_auth()
    }

    data = {
        'characterId' : characterId,
        'id' : id,
        'removeContainerContents' : False
    }
    data = json.dumps(data)

    res = requests.delete(URL_ITEM, data=data, headers=headers)
    return res.json()

def edit_item(characterId, customData):
    headers = {
        'Accept': '*/*', 
        'Content-Type': 'application/json;charset=utf-8', 
        'Authorization': 'Bearer ' + get_auth()
    }

    data = {
        'characterId' : characterId,
        'typeId' : customData['typeId'],
        'value' : customData['value'],
        'valueId' : customData['valueId'],
        'valueTypeId': customData['valueTypeId'],
        'notes' : customData['notes'],
        'contextId' : customData['contextId'],
        'contextTypeId' : customData['contextTypeId'],
        'partyId' : None
    }
    data = json.dumps(data)
    res = requests.put(URL_CUSTOM, data=data, headers=headers)

    return res.json()

def get_character(characterId):
    res = requests.get(URL_CHARACTER + str(characterId))
    return res.json()['data']

def give(charFromId, charToId, item, quantity, customData):
    res = add_item(charToId, item['definition']['id'], item['definition']['entityTypeId'], quantity)

    itemAddedId = res['data']['addItems'][0]['id']

    if res['success']:
        res = delete_item(charFromId, item['id'])
        if not res['success']:
            print("Error on deleting")
            print(res)
            return False
    else:
        print("Error on adding")
        print(res)
        return False
    
    for n, data in enumerate(customData):
        customData[n]['valueId'] = str(itemAddedId)
        res = edit_item(charToId, data)
        if not res['success']:
            print("Error on editing")
            print(res)
            return False

    return True

'''
Returns False if not enough balance, True if it's successful
'''
def modify_currency(characterId, cp=0, sp=0, ep=0, gp=0, pp=0):
    headers = {
        'Accept': '*/*', 
        'Content-Type': 'application/json;charset=utf-8', 
        'Authorization': 'Bearer ' + get_auth()
    }

    data = {
        'characterId' : characterId,
        'cp' : cp,
        'sp' : sp,
        'ep' : ep,
        'gp' : gp,
        'pp' : pp,
        'destinationEntityId' : characterId,
        'destinationEntityTypeId' : 1581111423 # Again this number pops up no idea why
    }
    data = json.dumps(data)

    res = requests.put(URL_TRANSACTION, headers=headers, data=data)

    if not res.json()['success']:
        return res.json()

    # Check if any currencies went into negatives, if so then reverse transaction
    for i in res.json()['data']:
        if res.json()['data'][i] < 0:
            # Reverse transaction
            data = {
                'characterId' : characterId,
                'cp' : cp * -1,
                'sp' : sp * -1,
                'ep' : ep * -1,
                'gp' : gp * -1,
                'pp' : pp * -1,
                'destinationEntityId' : characterId,
                'destinationEntityTypeId' : 1581111423 # Again this number pops up no idea why
            }
            data = json.dumps(data)

            res = requests.put(URL_TRANSACTION, headers=headers, data=data)
            return False

    return True

def pay(charFromId, charToId, cp=0, sp=0, ep=0, gp=0, pp=0):
    if cp < 0 or sp < 0 or ep < 0 or gp < 0 or pp < 0:
        return False
    if modify_currency(charFromId, cp*-1, sp*-1, ep*-1, gp*-1, pp*-1):
        modify_currency(charToId, cp, sp, ep, gp, pp)
        return True
    return False
