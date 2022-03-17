import os
from flask import Flask, redirect, url_for
import threading
import time
from threading import Thread
from requests.auth import HTTPBasicAuth
import requests
import json
from kafka import KafkaProducer
from datetime import datetime
import time
import schedule
import math

###PREPARED BY TCD###

env=os.environ.get("env")

class myThread (threading.Thread):
    #Starting Threads From Here
    def __init__(self, thread_name, host):
       threading.Thread.__init__(self)
       self.thread_name = thread_name
       self.host = host
       #self.counter = counter
          
    def run(self):
        #threadLock.acquire()
        print ("Starting " + self.thread_name)
        print ("The data will be retrieved for " + self.host)
        ldap_conn().get_request(self.host)
        #threadLock.release()

class ldap_conn(object):
    def __init__(self):
        self.x = 'Hello'

    def get_request(self, host_name):
        self.host_name = host_name
        while True:
            #Current Timestamp Calculating
            current_timestamp = str(int(math.floor(datetime.now().timestamp())*1000000000))
            current_timestamp = current_timestamp.strip()
            print("Current timestamp is: " + current_timestamp)
            #Kafka Info
            producer = KafkaProducer(bootstrap_servers=['klmetkfkt1.uatisbank:9092', 'klmetkfkt2.uatisbank:9092', 'klmetkfkt3.uatisbank:9092'])
            ldap_healtcheck_liberty="ldap_healtcheck_liberty"
            # Checking LDAP Connections of Servers and Sendind Datas to Kafka
            try:
                print("Trying to check the connection status for %s"%host_name)
                response4liberty = requests.get(('https://%s:9443/IBMJMXConnectorREST/mbeans/'%host_name), auth=HTTPBasicAuth('wassecadm', 'WASsec2013'), verify = False)            
                response4liberty_str = str(response4liberty.status_code)

                print("Status Code for LDAP Connection: " + response4liberty_str)
                
                if (response4liberty.status_code == 200):
                    print("LDAP connnection is succesful")
                    connection_info="ldap_healtcheck_liberty,Host=%s LDAP_connection_status=\"2\""%host_name
                    all_kafka_data=connection_info + " " + current_timestamp
                else:
                    print("There is no connection to LDAP from this server")
                    connection_info="ldap_healtcheck_liberty,Host=%s LDAP_connection_status=\"1\""%host_name
                    all_kafka_data=connection_info + " " + current_timestamp               
            except:
                print("An exceptional situation occured. There is connection problem")
                connection_info="ldap_healtcheck_liberty,Host=%s LDAP_connection_status=\"0\""%host_name
                all_kafka_data=connection_info + " " + current_timestamp
            print("The data that is sent to Kafka: " + all_kafka_data)    
            producer.send('custommon', bytes(all_kafka_data, 'utf-8'))    
            producer.flush()
            time.sleep(10)



class inventorius ():

    def inventorius_data (self):
    
        ### Fetching and Parsing Inventorius Data

        #This part is for the PROD inventorius

        if env == "PROD":

            response4inventorius_prod = requests.get('https://app.isbank/ahtapot/servers/api?field1=ownerGroup&value1=ISQ2ISUS&filed2=os&value2=Linux&field3=environment&value3=PROD', verify = False)        
            if (response4inventorius_prod.status_code == 200):
                print("Response is taken successfully from inventorius API")
            else:
                print("Inventorius API seems unreachable.")
                
            data = response4inventorius_prod.json()
            host_names = []
                
            for d in data:
                a = d['host']
                host_names.append(a)

            lib_filter_prod = ['wlpt']
            liberty_hosts = [x for x in host_names if all(y in x for y in lib_filter_prod)]
        
        #This part is for the UAT inventorius
        elif env == "UAT":
            response4inventorius_uat = requests.get('http://uygulama.isbank/service/information.php?service=server&tip=4&ortam=UAT', verify = False)
        
            response = response4inventorius_uat.text
            if (response4inventorius_uat.status_code == 200):
                print("Response is taken successfully from UAT inventorius API")
                
                data_parsing = response.strip()
                data_parsing = data_parsing.replace("UAT;4;","")
                data_parsing = data_parsing.replace("</br>"," ").strip()
                uat_hosts = list (data_parsing.split(" "))
                #print(uat_hosts)
                liberty_hosts = list(filter(lambda myfilter: 'wlpt' in myfilter, uat_hosts))     

            else:
                print("UAT Inventorius API seems unreachable.")

        else:
             print("Invalid env error") 

        # Defining Threads and Starting
        for host_uat in liberty_hosts:
            thread_number = int(liberty_hosts.index(host_uat)) + 1
            thread = myThread(('Thread-{}'.format(thread_number)), host_uat)
            thread.start()
            time.sleep(2)    
        # thread1 = myThread("Thread-1", "klomiwlpt2")
        # print ("Thraed_%s has just started working at %s"%(1,time.ctime(time.time())))
        # thread2 = myThread("Thread-2", "klcovkduwlpt2")
        # thread3 = myThread("Thread-2", "klcovkduwlpt1")
        # #print(liberty_hosts_prod)
        # thread1.start()
        # time.sleep(3)
        # thread2.start()
        # time.sleep(3)
        # thread3.start()
        
        # End-point To Check The App
        app = Flask(__name__)
        @app.route('/')
         
        def endpoint4app():
            data = '\n\nLDAP Health Check Application is running successfully.'
            print(data)
            return data
        port = int(os.environ.get('PORT', 8080))        
        app.run(host="0.0.0.0", port=port)  

run_app = inventorius()
run_app.inventorius_data()

###PREPARED BY TCD###                