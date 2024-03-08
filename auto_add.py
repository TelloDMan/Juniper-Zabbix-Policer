#!/usr/bin/python3
from auto_snmp import start_snmp
import re
from pyzabbix import ZabbixAPI#, ZabbixAPIException

#IP of THE ZABBIX SERVER
Zabbix_IP = '' 

Website = 'http://'+Zabbix_IP+'/zabbix/'
url = Website + 'api_jsonrpc.php'

# Zabbix API authentication details
user = ''
password = ''

# Headers for the HTTP request
headers = {'Content-Type': 'application/json-rpc'}

zapi = ZabbixAPI(Website)
zapi.login(user,password)

#HOSTNAME AS IT IS ON ZABBIX
host_name = "Zabbix Server" 
hosts = zapi.host.get(filter={"host": host_name},selectInterfaces=["interfaceid"])
host_id = hosts[0]["hostid"]

# Authentication payload
auth_payload = {
    'jsonrpc': '2.0',
    'method': 'user.login',
    'params': {
        'user': user,
        'password': password,
    },
    'id': 1,
}


priority = 1  # 0 - (default) not classified, 1 - information, 2 - warning, 3 - average, 4 - high, 5 - disaster

content = start_snmp()[1:]


    
trigger_data = zapi.trigger.get(hostids = host_id)

Inbound = [data for data in trigger_data if data['description'].split(' ')[1][0] == "I"]
Outbound = [data for data in trigger_data if data['description'].split(' ')[1][0] == "O"]

if len(Inbound) > 0:
    for entry in Inbound:
        interface = entry['description'].split(' ')[0]
        for policy in content:
            notpresent = True
            #match entries from the policing rules per subinterface
            try:
                settings = re.findall("\"limit.*\"$",policy)[0][1:-1].split("-") #['limit', '10m', 'xe', '0/0/0.10', 'inet', 'i']
            except:
                print(policy)
            if interface == settings[2] + "-" + settings[3]:
                notpresent = False
                limiting = policy
                description = settings[2] + '-' + settings[3] + " " + "Inbound " + settings[1]
                #match speed and calculate the bits for expression
                if settings[1][-1].lower() == 'm': 
                    limit = str(float(settings[1][:-1]) * 1000000)
                elif settings[1][-1].lower() == 'g':
                    limit = str(float(settings[1][:-1]) * 1000000000)
                #specifies the item key inside the expression which is created by a discovery rule
                expression = 'avg(/{host_name}/1.3.6.1.4.1.2636.3.3.1.1.1.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=settings[2] + '-' + settings[3], limit=limit)
                #remove already present triggers
                content.remove(policy)
                triggered = entry["triggerid"]
                #update entries for already available trigegrs
                trigger_update = zapi.trigger.update({
                        'triggerid': triggered,
                        'description': description,
                        'expression': expression,
                        'status': 0,  # 0 - enabled, 1 - disabled
                    })
                break
        if notpresent:
            #delete any trigger that does'nt have a subinterface 
            try:
                trigger_delete = zapi.trigger_delete(entry["triggerid"])
            except:
                print("Delete Failed",entry)

if len(Outbound) > 0:
    for entry in Outbound:
        interface = entry['description'].split(' ')[0]
        for policy in content:
            notpresent = True
            try:
                settings = re.findall("\"limit.*\"$",policy)[0][1:-1].split("-") #['limit', '10m', 'xe', '0/0/0.10', 'inet', 'i']
            except:
                print(policy)
            if interface == settings[2] + "-" + settings[3]:
                notpresent = False
                limiting = policy
                description = settings[2] + '-' + settings[3] + " " + "Outbound " + settings[1]
                if settings[1][-1].lower() == 'm': 
                    limit = str(float(settings[1][:-1]) * 1000000)
                elif settings[1][-1].lower() == 'g':
                    limit = str(float(settings[1][:-1]) * 1000000000)
                expression = 'avg(/{host_name}/1.3.6.1.4.1.2636.3.3.1.1.4.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=settings[2] + '-' + settings[3], limit=limit)
                content.remove(policy)
                triggered = entry["triggerid"]
                trigger_update = zapi.trigger.update({
                        'triggerid': triggered,
                        'description': description,
                        'expression': expression,
                        'status': 0,  # 0 - enabled, 1 - disabled
                    })
                break
        if notpresent:
            try:
                trigger_delete = zapi.trigger_delete(entry["triggerid"])
            except:
                print("Delete Failed",entry)



for policy in content:
    try:
        settings = re.findall("\"limit.*\"$",policy)[0][1:-1].split("-") #['limit', '10m', 'xe', '0/0/0.10', 'inet', 'i']
        interfaces = settings[2] + "-" + settings[3]
        if settings[-1] == "i":
            description = settings[2] + '-' + settings[3] + " " + "Inbound " + settings[1]
            limit = str(float(settings[1][:-1]) * 1000000)
            expression = 'avg(/{host_name}/1.3.6.1.4.1.2636.3.3.1.1.1.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=settings[2] + '-' + settings[3], limit=limit)

        elif settings[-1] == 'o':
            description = settings[2] + '-' + settings[3] + " " + "Outbound " + settings[1]
            limit = str(float(settings[1][:-1]) * 1000000)
            expression = 'avg(/{host_name}/1.3.6.1.4.1.2636.3.3.1.1.4.[{interface}],600s)>{limit}'.format(host_name=host_name, interface=settings[2] + '-' + settings[3], limit=limit)

        trigger_create = zapi.trigger.create({
            'description': description,
            'expression': expression,
            'priority': priority,
            'status': 0,  # 0 - enabled, 1 - disabled
            'type': 0,  # 0 - trigger, 1 - discovery
            'dependencies': [],
            })
    except:
         continue


zapi.user.logout()
