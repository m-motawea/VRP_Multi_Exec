# VRP_Multi_Exec
Automation Tool for Configuring Huawei VRP Devices

# Files used:
1- Targets file (required): which includes the devices IP addresses and login credentials.
```ini
[SITE1]
dev1 192.168.23.100 username Passwd12#$
20.20.20.101 username Passwd12#$

[SITE2]
10.10.10.101 username Passwd12#$ 
```

* in case you use `--password-promt` option or use `--keyfile`, you must remove the password value from this file

2- Variables file (optional): includes the variables which will be used to render the configuration file (if exists). It supports lists by separating values by “,” like the below “ifaces”.
```ini
[all]
int_name = ETH-Trunk1
ifaces = GE1/0/0,GE1/0/1

[SITE1]
int_name = Stack-Port1


[SITE1:192.168.23.100]
int_name = Stack-Port2
```

4- Run log file (generated): this is specified when executing the script to save a run log for all devices.

5- `multi_exec.json` file (generated): this is generated automatically after running the script. It is a more detailed log.


# Requirements:
Code dependencies are:
```Paramiko``` and ```Jinja2```. You can install them using the requirements file with the code.
```bash
$ pip3 install -r requirements.txt
```


# Build:
```bash
pip install -r requirements
pyinstaller --onefile multi_exec.py
```

# Usage:
```bash
Usage: multi_exec.exe [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  config  run generic config template
  exec    run generic config template
```
### Config command:

requires a configuration file in the below format that supports jinja2 template in its content or just plain commands to be executed in order.

```ini
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

example: 
```bash
multi_exec config targets.ini config.ini --variables vars.ini --password-prompt
```



* Group name followed by the execution order: [SITE1:2] means the following commands will be executed on SITE1 in order 2.
  
* .[all:1] “all” is used to execute on all targets defined. This means it will execute the following commands on all devices in order 1 (first).
  
* Note that in both configuration example the first command is “N” this to answer the login prompt for changing the password 




### exec command:
executes ad-hoc command on a specified group.
example: 
```bash
multi_exec exec targets.ini ls --variables vars.ini --password-prompt
```

to execute multiple commands use && between commands like, 
```bash
multi_exec exec targets.ini "ls && pwd" --variables vars.ini --password-prompt
```
    
