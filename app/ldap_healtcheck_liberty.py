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
import math


env = os.environ.get("env")
kafka_host1 = os.environ.get("kafka_host1")
kafka_host2 = os.environ.get("kafka_host2")
kafka_host3 = os.environ.get("kafka_host3")
api_password = os.environ.get("api_password")
bootstrap_servers=[kafka_host1, kafka_host2, kafka_host3]

class MyThread (threading.Thread):
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
        Ldap_conn().get_request(self.host)
        #threadLock.release()


class Ldap_conn(object): 
    def __init__(self):
        self.req_num = 0

    def get_request(self, host_name):
        self.host_name = host_name
        
        while True:
            time.sleep(3)
            
            try:
                self.req_num += 1
                #Current Timestamp Calculating
                current_timestamp = str(int(datetime.now().timestamp() * 1000000000))
                #current_timestamp = str(int(math.floor(datetime.now().timestamp())*1000000000))
                current_timestamp = current_timestamp.strip()
                
                print("Current timestamp: %s time: %s and  host name: %s" %(current_timestamp,time.ctime(time.time()),host_name)) 
                
                #Kafka Info
                producer = KafkaProducer(bootstrap_servers = bootstrap_servers, api_version = (0,9))  
                
                # Checking LDAP Connections of Servers and Sendind Datas to Kafka
                try:
                    print("Trying to check the connection status for %s"%host_name)
                    response4liberty = requests.get(('https://%s:9443/IBMJMXConnectorREST/mbeans/'%host_name), auth=HTTPBasicAuth('wassecadm', api_password), verify = False)            
                    response4liberty_str = str(response4liberty.status_code)

                    print("Status Code for LDAP Connection: " + response4liberty_str)
                    
                    if (response4liberty.status_code == 200):
                        print("LDAP connnection is succesful")
                        connection_info="ldap_healthcheck_liberty,Host=%s LDAP_connection_status=\"2\""%host_name
                        all_kafka_data=connection_info + " " + current_timestamp
                    else:
                        print("There is no connection to LDAP from this server")
                        connection_info="ldap_healthcheck_liberty,Host=%s LDAP_connection_status=\"1\""%host_name
                        all_kafka_data=connection_info + " " + current_timestamp               
                except:
                    print("An exceptional situation occured. There is connection problem")
                    connection_info="ldap_healthcheck_liberty,Host=%s LDAP_connection_status=\"0\""%host_name
                    all_kafka_data=connection_info + " " + current_timestamp
                print("The data that is sent to Kafka: %s ***  request number: %s"%(all_kafka_data,self.req_num))  
                producer.send('custommon', bytes(all_kafka_data, 'utf-8'))    
                producer.flush()
                time.sleep(28)
            except:
                print("Connections must be checked")


class Inventorius ():

    def inventorius_data (self):
    
        ### Fetching and Parsing Inventorius Data

        #This part is for the PROD inventorius

        if env == "PROD":

            response4inventorius_prod = requests.get('https://api_for_invontorius_PROD', verify = False)        
            if (response4inventorius_prod.status_code == 200):
                print("Response is taken successfully from inventorius API")
            else:
                print("Inventorius API seems unreachable.")
                
            data = response4inventorius_prod.json()
            host_names = []
                
            for d in data:
                a = d['host']
                host_names.append(a)

            lib_filter_prod = ['wlp']
            liberty_hosts = [x for x in host_names if all(y in x for y in lib_filter_prod)]
        
        #This part is for the UAT inventorius
        elif env == "UAT":
            response4inventorius_uat = requests.get('http://api_for_invontorius', verify = False)
        
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

        elif env == "INT":
            while True:
                print("App is disabled for INT environment.")
                time.sleep(3600)

        else:
             print("Invalid env error") 

        # Defining Threads and Starting
        for host_for_screen in liberty_hosts:
            thread_number = int(liberty_hosts.index(host_for_screen)) + 1
            thread = MyThread(('Thread-{}'.format(thread_number)), host_for_screen)
            thread.start()
            time.sleep(2)    
        # thread1 = MyThread("Thread-1", "klomiwlpt2")

        # thread2 = MyThread("Thread-2", "klcovkduwlpt2")
        # thread3 = MyThread("Thread-2", "klcovkduwlpt1")

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
            print("TCD was here")
            print(data)
            return data
        port = int(os.environ.get('PORT', 8080))        
        app.run(host="0.0.0.0", port=port)  

run_app = Inventorius()
run_app.Inventorius_data()

###PREPARED BY Taha Çağrıhan Dülgar###                
