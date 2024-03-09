#!/usr/bin/python3
import subprocess

community = ""  #YOUR #COMMUNITY #STRING
Target = "" #YOUR TARGET DEVICE IP # 192.168.1.1

def start_snmp():
	#snmpwalk into the PE Router Policers
	content = subprocess.run(["snmpwalk" ,"-v2c", "-c", community ,Target+":161", "1.3.6.1.4.1.2636.3.5.2.1.7"],capture_output=True)

	#split content
	content = content.stdout.decode("utf-8")

	#split the content
	content = content.split("\n")

	return content






