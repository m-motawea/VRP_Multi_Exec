# VRP_Multi_Exec
Automation Tool for Configuring Huawei VRP Devices

# Required Files:
1- Targets file: which includes the devices IP addresses and login credentials.
```
[SITE1]
192.168.23.100 username Passwd12#$
20.20.20.101 username Passwd12#$

[SITE2]
10.10.10.101 username Passwd12#$ 
```

2- Variables file: includes the variables which will be used to render the configuration file (if exists). It supports lists by separating values by “,” like the below “ifaces”.
```
[all]
int_name = ETH-Trunk1
ifaces = GE1/0/0,GE1/0/1

[SITE1]
int_name = Stack-Port1


[SITE1:192.168.23.100]
int_name = Stack-Port2
```

3- Configuration file: in jinja2 template format or just plain commands to be executed in order.
```
[all:1]
N
screen-len 0 temp
disp int br | inc {{ int_name }}

{% for iface_name in ifaces %}
disp lldp ne br | inc {{ iface_name }}
{% endfor %}

[SITE1:2]
N
save
y
```

  • Group name followed by the execution order: [PA3:2] means the following commands will be executed on PA3 in order 2.
  
  • .[all:1] “all” is used to execute on all targets defined. This means it will execute the following commands on all devices in order 1 (first).
  
  • Note that in both configuration example the first command is “N” this to answer the login prompt for changing the password

4- Run log file: this is specified when executing the script to save a run log for all devices.

5- “multi_exec.json” file: this is generated automatically after running the script. It is a more detailed log.

# How to Use:
```usage: multi_exec [-h] -t TARGETS [-c CONFIG] [-v VARS] [-m MODULE] [-a ARGS] [-o OUTPUT]```
  ## example:
  ```.\multi_exec.py -t targets.ini -c config.ini -v vars.ini -o run_log```

# Requirements:
Code dependencies are:
```Paramiko``` and ```Jinja2```. You can install them using the requirements file with the code.
```pip install -r requirements.txt```

    • This tool is developed and tested using Python3.7 but it should be compatible with Python2.x/3.x (not tested).
