import os
import json
import csv

'''
This script assumes it's being run in a directory
with a folder named "data", which holds all JSON.
'''

def pivotAccount(data, mapping) :
    record = {}
    for field in mapping :
        record[field] = data[field]
    return record

def pivotData(data, mapping, accountId) :
    records = []
    for row in data :
        record = { 'AccountId' : accountId }
        for field in mapping :
            record[field] = row[field]
        records.append(record)
    return records

def pivotContacts(data, mapping) :
    records = []

    people = data.get('people')
    for person in people :
        record = { 'AccountId' : data.get("id")}

        # pivot all basic field data
        for field in mapping :
            if "." in field :
                field = field.split('.')[1]
                record[field] = person[field]
            else :
                record[field] = person[field]

        # special pivot address data
        addresses = person.get("addresses", [])
        if len(addresses) > 0 :
            # loop over all emails looking for primary address
            primaryFound = False
            for address in addresses :
                if address.get('is_primary') :
                    record['BillingStreet'] = address.get('line1', '')
                    record['BillingCity'] = address.get('city')
                    record['BillingState'] = address.get('state')
                    record['BillingPostalCode'] = address.get('zip')
                    record['BillingCountry'] = address.get('country_code') 
                    primaryFound = True
                    break
            # use first address if no primary address found
            if not primaryFound :
                record['BillingStreet'] = addresses[0].get('line1', '')
                record['BillingCity'] = addresses[0].get('city')
                record['BillingState'] = addresses[0].get('state')
                record['BillingPostalCode'] = addresses[0].get('zip')
                record['BillingCountry'] = addresses[0].get('country_code') 
        else : 
            record['BillingStreet'] = ''
            record['BillingCity'] = ''
            record['BillingState'] = ''
            record['BillingPostalCode'] = ''
            record['BillingCountry'] = ''

        # special pivot email data
        emails = person.get('email_addresses', [])
        if len(emails) > 0 :
            # loop over all emails looking for primary address
            primaryFound = False
            for address in emails :
                if address.get('is_primary') :
                    record['Email'] = address.get('email', None)
                    primaryFound = True
                    break
            # use first address if no primary address found
            if not primaryFound :
                record['Email'] = emails[0].get('email', None)
        else : 
            record['Email'] = None

        # special pivot phone data
        numbers = person.get('phone_numbers', [])
        if len(numbers) > 0 :
            # loop over all numbers looking for primary phone
            primaryFound = False
            for number in numbers :
                if number.get('is_primary') :
                    record['Phone'] = number.get('unformatted_phone', None)
                    primaryFound = True
                    break
            # use first number if no primary number found
            if not primaryFound :
                record['Phone'] = numbers[0].get('unformatted_phone', None)
        else :
            record['Phone'] = None
        
        # special pivot employment data
        employments = person.get("employments")
        if len(employments) > 0 :
            for job in employments :
                if job.get("actively_employed") :
                    record['Employment_Status__c'] = "Employed"
                    record['Occupation__c'] = job.get("role", None)
                    record['Employer__c'] = job.get("business_name")
                    break
                else :
                    record['Employment_Status__c'] = None
                    record['Occupation__c'] = None
                    record['Employer__c'] = None
        else :
            record['Employment_Status__c'] = False
            record['Occupation__c'] = None
            record['Employer__c'] = None
        
        records.append(record)

    return records


# returns map of all employments, addresses, phones, and emails that exist in this account file
def pivotContactSubrecords(data) :
    records = {
        'addresses'     : [],
        'emails'        : [],
        'employments'   : [],
        'phones'        : []
    }

    people = data.get('people')
    for person in people :
        # collect all address data
        addresses = person.get("addresses", [])
        if len(addresses) > 0 :
            for address in addresses :
                record = {
                    'account_id'     : data.get('id'),
                    'contact_id'     : person.get('id'),
                    'line1'          : address.get('line1', ''),
                    'line2'          : address.get('line2', ''),
                    'city'           : address.get('city', ''),
                    'state'          : address.get('state', ''),
                    'zip'            : address.get('zip', ''),
                    'country_code:'  : address.get('country_code', ''),
                    'address_type'   : address.get('address_type', ''),
                    'is_primary'     : address.get('is_primary', '')
                }
                records['addresses'].append(record)
        
        # special pivot email data  
        emails = person.get('email_addresses', [])
        if len(emails) > 0 :
            for address in emails :
                record = {
                    'account_id'     : data.get('id'),
                    'contact_id'     : person.get('id'),
                    'email'          : address.get('email', ''),
                    'email_type'     : address.get('email_type', ''),
                    'is_primary'     : address.get('is_primary', '')
                }
                records['emails'].append(record)

        # special pivot phone data
        numbers = person.get('phone_numbers', [])
        if len(numbers) > 0 :
            for number in numbers :
                record = {
                    'account_id'        : data.get('id'),
                    'contact_id'        : person.get('id'),
                    'unformatted_phone' : number.get('unformatted_phone', ''),
                    'phone_type'        : number.get('phone_type', ''),
                    'is_primary'        : number.get('is_primary', '')
                }
                records['phones'].append(record)
        
        # special pivot employment data
        # contact_id, account_id, business_name, business_id, role, start_date, end_date, actively_employed
        employments = person.get("employments")
        if len(employments) > 0 :
            for job in employments :
                record = {
                    'account_id'        : data.get('id'),
                    'contact_id'        : person.get('id'),
                    'business_name'     : job.get('business_name', ''),
                    'business_id'       : job.get('business_id', ''),
                    'start_date:'       : job.get('start_date', ''),
                    'end_date'          : job.get('end_date', ''),
                    'actively_employed' : job.get('actively_employed', '')
                }
                records['employments'].append(record)

    return records


def generateCsv(fileName, mapping, data) :
    with open('results/' + fileName, 'w', newline='') as csv_file :
        fieldnames = mapping
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in data :
            writer.writerow(row)

'''
    initializes "mappings" map by scanning the JSON and noting all available fields.

    to determine the mappings for each object, we initially scan for ALL field names / JSON
    object keys. since certain fields are arrays of sub-objects that we want to export as 
    separate files, we do not include them in the parent object's extraction by manually 
    removing the relevant arrays from the top-level keys we initally scanned into the map.

    we are left with a map of strings (the name of the object to export) that point to
    and array of strings (the names of each field in the JSON that we want to export for
    said object)

    lastly, since I couldn't find a JSON file that had an entry for every single object
    we wanted to export, we have to scan two separate files to determine all field names
    for this data set. you will need as many "with open" statements as files that you've
    looked at and have determined have values for each relevant object!

'''
def establishMappings() :
    print('establishing mappings..')

    mappings = {}
    # this file has a data point for almost every possible column/field except for "opportunities"
    with open('data/albrecht-kurt-ann_kHkGYNVT1L.json', 'r', newline='') as data :
        data = json.loads(data.read())
        # to determine account mappings, we'll take all top-level fields to cast a broad net
        mappings["account"]      = list(data.keys())
        # all contact objects are in the "people" array
        mappings["contact"]      = list(data["people"][0].keys())
        # all 
        mappings["note"]         = list(data["notes"][0].keys())
        mappings["task"]         = list(data["tasks"][0].keys())
        mappings["meeting"]      = list(data["meetings"][0].keys())
    # we use this file to determine the opportunity field names
    with open('data/alli-daniel-household_XQXUDLAXbo.json', 'r', newline='') as data :
        data = json.loads(data.read())
        mappings["opportunity"]  = list(data["opportunities"][0].keys())

    # clean mappings up for use!
    #  to rephrase:
    # arrays/sub-objects fields get removed from the mapping defintion so 
    # their data is skipped when extracting parent object data from the files
    mappings["account"].remove("people")
    mappings["account"].remove("notes")
    mappings["account"].remove("tasks")
    mappings["account"].remove("meetings")
    mappings["account"].remove("opportunities")

    mappings["contact"].remove('email_addresses')
    mappings["contact"].remove('phone_numbers')
    mappings["contact"].remove('addresses')
    mappings["contact"].remove('employments')

    mappings["meeting"].remove('transcript')

    print('mappings established!')

    return mappings

'''
    certain fields get added to the exported records during the
    pivoting/parsing process that the mappings aren't aware of. the easiest
    way to create the CSV headers is to use the mapping file- because
    it already has all of the relevant field names in it- but first,
    we have to add those custom fields we included during pivoting.
'''
def convertMappingsToCsvHeaders(mappings) :
    # lookups to Account ID were added on most objects
    mappings["contact"].append("AccountId")
    mappings["note"].append("AccountId")
    mappings["task"].append("AccountId")
    mappings["meeting"].append("AccountId")
    mappings["opportunity"].append("AccountId")
    
    # since Email/Phone in salesforce can only hold one value, we changed
    # the name of the "email_addresses"/"phone_numbers" columns
    mappings["contact"].append("Email") 
    mappings["contact"].append("Phone")
    
    # same idea with address information
    mappings["contact"].append("BillingStreet") 
    mappings["contact"].append("BillingCity") 
    mappings["contact"].append("BillingState") 
    mappings["contact"].append("BillingPostalCode") 
    mappings["contact"].append("BillingCountry") 
    # and employment information
    mappings["contact"].append("Employment_Status__c") 
    mappings["contact"].append("Occupation__c") 
    mappings["contact"].append("Employer__c")

    print('CSV headers ready!')

    return mappings


def main() :
    # first determine our field mappings so we know which JSON fields belong to each object
    mappings = establishMappings()

    # prepare arrays for each object that gets an extraction
    accounts      = []
    contacts      = []
    tasks         = []
    notes         = []
    meetings      = []
    opportunities = []
  
    emails        = []
    phones        = []
    addresses     = []
    employments   = []

    # read through every JSON file in the directory to extract/organize data types into arrays
    fileCount = 1
    fileNames = os.listdir('data')
    for fileName in fileNames :
        
        print('parsing file ', fileCount, ' ', fileName, sep=' ')
        
        fileName = 'data/' + fileName
        with open(fileName, 'r', newline='') as data :
            data = json.loads(data.read())
            accountId = data["id"]

            ''' EXTRACT ACCOUNT DATA '''
            accounts.append(pivotAccount(data, mappings["account"]))
            ''' EXTRACT CONTACT DATA '''
            contacts.extend(pivotContacts(data, mappings["contact"]))
            ''' EXTRACT TASK DATA '''
            tasks.extend(pivotData(data.get("tasks"), mappings["task"], accountId))
            ''' EXTRACT NOTES DATA '''
            notes.extend(pivotData(data.get("notes"), mappings["note"], accountId))
            ''' EXTRACT MEETING DATA '''
            meetings.extend(pivotData(data.get("meetings"), mappings["meeting"], accountId))
            ''' EXTRACT OPPORTUNITY DATA '''
            opportunities.extend(pivotData(data.get("opportunities"), mappings["opportunity"], accountId))

            ''' EXTRACT CONTACT SUB-RECORD VALUES '''
            results = pivotContactSubrecords(data)
            addresses.extend(results.get('addresses', []))
            emails.extend(results.get('emails', []))
            phones.extend(results.get('phones', []))
            employments.extend(results.get('employments', []))

            fileCount = fileCount + 1

    # prepare headers for CSV export
    csvHeaders = convertMappingsToCsvHeaders(mappings)

    # use lists of data to create CSVs
    generateCsv('accounts.csv',      csvHeaders["account"],     accounts)
    generateCsv('contacts.csv',      csvHeaders["contact"],     contacts)
    generateCsv('tasks.csv',         csvHeaders["task"],        tasks)
    generateCsv('notes.csv',         csvHeaders["note"],        notes)
    generateCsv('meetings.csv',      csvHeaders["meeting"],     meetings)
    generateCsv('opportunities.csv', csvHeaders["opportunity"], opportunities)

    generateCsv('emails.csv',        list(emails[0].keys()),      emails)
    generateCsv('phones.csv',        list(phones[0].keys()),      phones)
    generateCsv('addresses.csv',     list(addresses[0].keys()),   addresses)
    generateCsv('employments.csv',   list(employments[0].keys()), employments)

    print('done! ', fileCount, ' files scanned')



if __name__=="__main__":
    main()