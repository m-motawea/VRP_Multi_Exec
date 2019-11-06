from lib.ssh_tools import BaseConnection
from lib.config_parser import ConfigParser
import datetime

class ConfigHandler(object):
    def __init__(self, config_file_path, is_ordered=True):
        self.config_groups = self.get_config_groups(config_file_path)
        self.is_ordered = is_ordered

    def get_config_groups(self, config_file_path):
        with open("config.ini", "r") as config_file:
            config_text = "\n".join(config_file.readlines())
        self.config_parser = ConfigParser()
        config_groups = self.config_parser.parse(config_text)
        return config_groups

    def execute_config(self, target_groups, log_level=1, out_file=None):
        """
        :param target_groups: obtained by parsing the targets file by lib.targets_parser.TargetParser
        :param log_level: between 0 - 1
        :param out_file: output file path. default (datetime.datetime.now().result.log)
        :return:
        """
        json_result = []
        ordered_group_config = self.config_parser.order(self.config_groups)
        #print("ordered groups")
        #print(ordered_group_config)
        #print("\n\n")
        for group_config in ordered_group_config:
            execution_devices = []
            if group_config["name"].split(":")[0] == "all":
                for device_list in target_groups.values():
                    execution_devices += device_list
            else:
                execution_devices = target_groups[group_config["name"].split(":")[0]]

            for device in execution_devices:
                device_log = ""
                result_dict = {
                    "name": device.get("name", "UNSPECIFIED"),
                    "ip": device["ip"],
                    "username": device["username"],
                }
                conn = BaseConnection(
                    ip=device["ip"],
                    username=device["username"],
                    password=device["password"],
                    hostname=device.get("name", "")
                )
                print("connecting to device {}, ip: {}...".format(device.get("name", "UNSPECIFIED"), device["ip"]))

                try:
                    conn.connect()
                    device_shell = conn.get_shell()
                except Exception as e:
                    log_line = "execption {} when connecting to device.".format(str(e))
                    print(log_line)
                    result_dict["success"] = False
                    result_dict["result"] = log_line
                    continue

                # TODO render CMDs with host variables
                # From the (to be created) HostConfigRenderer Class
                # replace the below group_config with host_config list returned by the HostConfigRenderer Class
                for cmd in group_config["config"]:
                    print("cmd: {}".format(cmd))

                    try:
                        out = conn.shell_exec(device_shell, cmd)
                        print(out)
                        device_log += out
                    except Exception as e:
                        log_line = "failed to execute <{}> due to execption: {}\nskipping this device".format(cmd, str(e))
                        print(log_line)
                        result_dict["success"] = False
                        result_dict["result"] = device_log
                        try:
                            conn.close()
                        except:
                            pass
                        break
                result_dict["result"] = device_log
                result_dict["success"] = True
                json_result.append(result_dict)
                try:
                    conn.close()
                except:
                    pass


        with open(out_file, "w") as log:
            for result_dict in json_result:
                log.write("#############################################################################\n")
                log.write("DEVICE {}, IP {}, USERNAME {}, SUCCESS {}\n".format(
                    result_dict["name"],
                    result_dict["ip"],
                    result_dict["username"],
                    result_dict["success"]
                ))
                log.write(result_dict["result"])

        return json_result
