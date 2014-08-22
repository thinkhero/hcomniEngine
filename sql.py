import psycopg2, psycopg2.extras
import csv
import datetime
from rpcclient import *

def sql_connect():
    global con
    try:
      with open('/home/'+USER+'/.omni/sql.conf') as fp:
        DBPORT="5432"
        for line in fp:
          #print line
          if line.split('=')[0] == "sqluser":
            DBUSER=line.split('=')[1].strip()
          elif line.split('=')[0] == "sqlpassword":
            DBPASS=line.split('=')[1].strip()
          elif line.split('=')[0] == "sqlconnect":
            DBHOST=line.split('=')[1].strip()
          elif line.split('=')[0] == "sqlport":
            DBPORT=line.split('=')[1].strip()
          elif line.split('=')[0] == "sqldatabase":
            DBNAME=line.split('=')[1].strip()
    except IOError as e:
      response='{"error": "Unable to load sql config file. Please Notify Site Administrator"}'
      return response

    try:     
        con = psycopg2.connect(database=DBNAME, user=DBUSER, password=DBPASS, host=DBHOST, port=DBPORT)
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
    	return cur
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    
        sys.exit(1)

def select(dbc):
    try:
      dbc.execute("select * from transactions")
      ROWS= dbc.fetchall()
      print len(ROWS)
      print ROWS
    except psycopg2.DatabaseError, e:
      print 'Error %s' % e

def insert_tx(dbc, rawtx, protocol, blockheight, seq):
    TxHash = rawtx['result']['txid']
    TxBlockTime = datetime.datetime.utcfromtimestamp(rawtx['result']['blocktime'])
    TxErrorCode = rawtx['error']
    TxSeqInBlock= seq

    if protocol == "Bitcoin":
      #Bitcoin is only simple send, type 0
      TxType=0
      TxVersion=0
      TxState= "True"
      Ecosystem= "Production"
      TxSubmitTime = datetime.datetime.utcfromtimestamp(rawtx['result']['time'])

    elif protocol == "Mastercoin":
      #currently type a text output from mastercore 'Simple Send' and version is unknown
      TxType= get_TxType(rawtx['result']['type'])
      TxVersion= 0
      TxState= rawtx['result']['valid']
      #Use block time - 10 minutes to approx
      TxSubmitTime = TxBlockTime-datetime.timedelta(minutes=10)
      if rawtx['result']['propertyid'] == 2 or ( rawtx['result']['propertyid'] >= 2147483651 and rawtx['result']['propertyid'] <= 4294967295 ):
        Ecosystem= "Test"
      else:
        Ecosystem= "Production"

    else:
      print "Wrong protocol? Exiting, goodbye."
      exit(1)

    try:
        dbc.execute("INSERT into transactions "
                    "(TxHash, protocol, TxType, TxVersion, Ecosystem, TxSubmitTime, TxState, TxErrorCode, TxBlockNumber, TxSeqInBlock, TxBlockTime ) "
                    "VALUES (decode(%s,'hex'),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", 
                    (TxHash, protocol, TxType, TxVersion, Ecosystem, TxSubmitTime, TxState, TxErrorCode, TxBlockNumber, TxSeqInBlock, TxBlockTime))
        con.commit()
        #need validation on structure
        dbc.execute("Select dbtxserial from transacations where txhash=decode(%s, 'hex')", TxHash)
        serial=dbc.fetchall()['0']['dbtxserial']
        return serial
    except psycopg2.DatabaseError, e:
	if con:
            con.rollback()
	print 'Error %s' % e
        sys.exit(1)

def dumptxaddr_csv(csvwb, rawtx, protocol, host):
    TxHash = rawtx['result']['txid']

    if protocol == "Bitcoin":
      PropertyID=0
      #process all outputs
      for output in rawtx['result']['vout']:
        AddressRole="recipient"
	AddressTxIndex=output['n']
        #store values as satoshi/willits etc''. Client converts
	BalanceAvailableCreditDebit=int(output['value']*1e8)
        #multisigs have more than 1 address, make sure we find/credit all multisigs for a tx
        for addr in output['scriptPubKey']['addresses']:
          row={'Address': addr, 'PropertyID': PropertyID, 'TxHash': TxHash, 'protocol': protocol, 'AddressTxIndex': AddressTxIndex, 
               'AddressRole': AddressRole, 'BalanceAvailableCreditDebit': BalanceAvailableCreditDebit}
          csvwb.writerow(row)
      #process all inputs, Start AddressTxIndex=0 since inputs don't have a Index number in json and iterate for each input
      AddressTxIndex=0
      for input in rawtx['result']['vin']:
        AddressRole="sender"
        #existing json doesn't have raw address only prev tx. Get prev tx to decipher address/values
        prevtx=getrawtransaction(input['txid'])
        BalanceAvailableCreditDebit=int(prevtx['result']['vout'][input['vout']]['value'] * 1e8 * -1)
        #multisigs have more than 1 address, make sure we find/credit all multisigs for a tx
        for addr in prevtx['result']['vout'][input['vout']]['scriptPubKey']['addresses']:
          row={'Address': addr, 'PropertyID': PropertyID, 'TxHash': TxHash, 'protocol': protocol, 'AddressTxIndex': AddressTxIndex,
               'AddressRole': AddressRole, 'BalanceAvailableCreditDebit': BalanceAvailableCreditDebit}
          csvwb.writerow(row)
        AddressTxIndex+=1

    elif protocol == "Mastercoin":
      PropertyID= rawtx['result']['propertyid']
      AddressTxIndex=0
      type=get_TxType(rawtx['result']['type'])

      if rawtx['result']['divisible']:
        value=int(rawtx['result']['amount']*1e8)
      else:
        value=int(rawtx['result']['amount'])

      #Simple Send
      if type == 0:
        Sender = rawtx['result']['sendingaddress']
        Reciever = rawtx['result']['referenceaddress']


    address
    #TxDBSerialNum  - initially empty for csv, will need to add relevant calls for sql
    AddressTxIndex
    AddressRole
    BalanceAvailableCreditDebit
    BalanceResForOfferCreditDebit
    BalanceResForAcceptCreditDebit
    protocol


def dumptx_csv(csvwb, rawtx, protocol, block_height, seq):
    TxHash = rawtx['result']['txid']
    TxBlockTime = datetime.datetime.utcfromtimestamp(rawtx['result']['blocktime'])
    TxErrorCode = rawtx['error']
    TxSeqInBlock= seq

    if protocol == "Bitcoin":
      #Bitcoin is only simple send, type 0
      TxType=0
      TxVersion=0
      TxState= "valid"
      Ecosystem= "Production"
      TxSubmitTime = datetime.datetime.utcfromtimestamp(rawtx['result']['time'])

    elif protocol == "Mastercoin":
      #currently type a text output from mastercore 'Simple Send' and version is unknown
      TxType= get_TxType(rawtx['result']['type'])
      TxVersion= 0
      TxState= rawtx['result']['valid']
      #Use block time - 10 minutes to approx
      TxSubmitTime = TxBlockTime-datetime.timedelta(minutes=10)
      if rawtx['result']['propertyid'] == 2 or ( rawtx['result']['propertyid'] >= 2147483651 and rawtx['result']['propertyid'] <= 4294967295 ):
        Ecosystem= "Test"
      else:
        Ecosystem= "Production"

    else:
      print "Wrong protocol? Exiting, goodbye."
      exit(1)

    row={'TxHash': TxHash, 'protocol': protocol, 'TxType': TxType, 'TxVersion': TxVersion, 'Ecosystem': Ecosystem, 
         'TxSubmitTime': TxSubmitTime, 'TxState': TxState, 'TxErrorCode': TxErrorCode, 'TxBlockNumber': block_height, 
         'TxSeqInBlock': TxSeqInBlock, 'TxBlockTime': TxBlockTime}
    #, 'TxMsg': rawtx}
    csvwb.writerow(row)


def get_TxType(text_type):
    convert={"Simple Send": 0 ,
             "Restricted Send": 2,
             "Send To Owners": 3,
             "Automatic Dispensary":-1,
             "DEx Sell Offer": 20,
             "MetaDEx: Offer/Accept one Master Protocol Coins for another": 21,
             "DEx Accept Offer": 22,
             "Create Property - Fixed": 50,
             "Create Property - Variable": 51,
             "Promote Property": 52,
             "Close Crowsale": 53
           }
    return convert[text_type]