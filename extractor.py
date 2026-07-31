import os
import json
import csv


def loadMapping(mappingPath) :
    mapping = {}
    with open (mappingPath, 'r') as f :
        reader = csv.DictReader(f)
        for row in reader :
            mapping[row['target_field']] = row['destination_field']
    return mapping


def pivotAccount(data, mapping) :
    record = {}
    for target_field in mapping.keys() :
        destination_field = mapping[target_field]
        record[destination_field] = data[target_field]
    return record

def pivotContacts(data, mapping) :
    record = {}

    people = data.get('people')
    for person in people :

        # pivot all basic field data
        for target_field in mapping.keys() :
            destination_field = mapping[target_field]
            
            if "." in target_field :
                target_field = target_field.split('.')[1]
                record[destination_field] = person[target_field]
            else :
                record[destination_field] = data[target_field]


        # pivot email data
        addresses = person.get('email_addresses', [])
        if len(addresses) > 0 :
            # loop over all emails looking for primary address
            primaryFound = False
            for address in addresses :
                if address.get('is_primary') :
                    record['Email'] = address.get('email', '')
                    primaryFound = True
                    break
            # use first address if no primary address found
            if not primaryFound :
                record['Email'] = addresses[0].get('email', '')
        else : 
            record['Email'] = ''

        # pivot phone data
        numbers = person.get('phone_numbers', [])
        if len(numbers) > 0 :
            # loop over all numbers looking for primary phone
            primaryFound = False
            for number in numbers :
                if number.get('is_primary') :
                    record['Phone'] = number.get('unformatted_phone', '')
                    primaryFound = True
                    break
            # use first number if no primary number found
            if not primaryFound :
                record['Phone'] = numbers[0].get('unformatted_phone', '')
        else :
            record['Phone'] = ''

    return record


def main() :

    account_mapping = loadMapping('mappings/account_mapping.csv')
    contact_mapping = loadMapping('mappings/contact_mapping.csv')
    
    ''' confirm mappings '''
    # for targetField in account_mapping.keys() :
    #     destinationField = account_mapping[targetField]
    #     print(f"{targetField} translates to {destinationField}")

    # for targetField in contact_mapping.keys() :
    #     destinationField = contact_mapping[targetField]
    #     print(f"{targetField} translates to {destinationField}")

    accounts  = []
    contacts  = []
    tasks     = []
    notes     = []
    meetings  = []

    ''' READ THROUGH ALL JSON FILES '''
    fileNames = os.listdir('data')
    for fileName in fileNames :
        fileName = 'data/' + fileName
        with open(fileName, 'r', newline='') as data :
            data = json.loads(data.read())
            ''' EXTRACT ACCOUNT DATA '''
            accounts.append(pivotAccount(data, account_mapping))
            ''' EXTRACT CONTACT DATA '''
            contacts.append(pivotContacts(data, contact_mapping))

    ''' CREATE "ACCOUNT" IMPORT CSV FILE '''
    with open('accounts.csv', 'w', newline='') as csv_file :
        fieldnames = account_mapping.values()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for account in accounts :
            writer.writerow(account)

    ''' CREATE "CONTACT" IMPORT CSV FILE '''
    with open('contacts.csv', 'w', newline='') as csv_file :
        fieldnames = list(contact_mapping.values())
        fieldnames.append('Email') # email is specially pivoted and won't be in source mapping file
        fieldnames.append('Phone') # phone is specially pivoted and won't be in source mapping file
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for contact in contacts :
            writer.writerow(contact)

            



if __name__=="__main__":
    main()




# the following snippet was used to extract all field names for each object
'''
    accountKeys = []
    contactKeys = []
    noteKeys    = []
    taskKeys    = []
    meetingKeys = []

    with open('data/albrecht-kurt-ann_kHkGYNVT1L.json', 'r', newline='') as data :
        data = json.loads(data.read())
        accountKeys = data.keys()
        contactKeys = data["people"][0].keys()
        noteKeys    = data["notes"][0].keys()
        taskKeys    = data["tasks"][0].keys()
        meetingKeys = data["meetings"][0].keys()

    for key in accountKeys :
        print(key, end=',')
    print()
    for key in contactKeys :
        print(key, end=',')
    print()
    for key in noteKeys :
        print(key, end=',')
    print()
    for key in taskKeys :
        print(key, end=',')
    print()
    for key in meetingKeys :
        print(key, end=',')
    print()

    return
'''