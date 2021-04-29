from lib.parsers.config import ConfigParserFactory
from lib.ssh_tools import NetworkDeviceConnection
from jinja2 import Template
import datetime
import gevent


class ConfigHandler(object):
    def __init__(self, logger, config_file_path, group=None):
        """Used to apply configuration template.

        Args:
            logger (loguru.logger): logger instance.
            config_file_path (str): path to the configuration file for config command.
            group ([str], optional): targets group name to execute on. Defaults to None.
        """
        self.logger = logger
        parser_factory = ConfigParserFactory(config_file_path)
        self.config_parser = parser_factory.parser
        self.config_groups = self.config_parser.parse()
        self.group = group

    def execute_config(
        self,
        target_groups,
        out_file=None,
        var_tree=None,
        sequential=False,
        timeout=2,
        write_result=True,
    ):
        out_file = out_file or f"exec_{datetime.datetime.now().timestamp()}.txt"
        var_tree = var_tree or {}
        json_result = []
        ordered_group_config = self.config_parser.order()

        host_tree = {}
        if var_tree:
            for group in var_tree:
                for host in var_tree[group]:
                    host_tree[host] = var_tree[group][host]

        for group_config in ordered_group_config:
            execution_devices = []
            group_name = group_config["name"].split(":")[0]
            if self.group and group_name != self.group:
                continue
            if group_name == "all":
                for device_list in target_groups.values():
                    execution_devices += device_list
            else:
                target_group_name = group_config["name"].split(":")[0]
                execution_devices = target_groups.get(target_group_name, [])
                if not execution_devices:
                    self.logger.warning(
                        f"group: {target_group_name} doesn't contain any devices"
                    )

            run_threads = []
            if sequential:
                for device in execution_devices:
                    self._device_exec(
                        device, json_result, var_tree, host_tree, group_config, timeout
                    )
            else:
                for device in execution_devices:
                    run_threads.append(
                        gevent.spawn(
                            self._device_exec,
                            device,
                            json_result,
                            var_tree,
                            host_tree,
                            group_config,
                            timeout,
                        )
                    )
                gevent.joinall(run_threads)

        if not write_result:
            return json_result

        with open(out_file, "w") as log:
            for result_dict in json_result:
                log.write(
                    "\n#############################################################################\n"
                )
                log.write(
                    "DEVICE {}, IP {}, USERNAME {}, SUCCESS {}\n".format(
                        result_dict["name"],
                        result_dict["ip"],
                        result_dict["username"],
                        result_dict["success"],
                    )
                )
                log.write(
                    "#############################################################################\n"
                )
                log.write(result_dict["result"])

        return json_result

    def _device_exec(
        self, device, json_result, var_tree, host_tree, group_config, timeout
    ):
        device_log = ""
        result_dict = {
            "name": device.get("name", "UNSPECIFIED"),
            "ip": device["ip"],
            "username": device["username"],
        }
        self.logger.info(
            "connecting to device {}, ip: {}...".format(
                device.get("name", "UNSPECIFIED"), device["ip"]
            )
        )

        try:
            conn = NetworkDeviceConnection(
                ip=device["ip"],
                username=device["username"],
                password=device["password"],
                key_path=device["key_filename"],
                hostname=device.get("name", ""),
            )
            conn.connect()
        except Exception as e:
            log_line = "execption {} when connecting to device.".format(str(e))
            self.logger.critical(log_line)
            result_dict["success"] = False
            result_dict["result"] = log_line
            json_result.append(result_dict)
            return

        config_template = Template("\n".join(group_config["config"]))
        if not var_tree:
            config_text = config_template.render()
        else:
            config_text = config_template.render(**host_tree.get(device["ip"], {}))

        for cmd in config_text.splitlines():
            self.logger.debug("ip: {} running cmd: {}".format(device["ip"], cmd))

            try:
                out, err = conn.exec(cmd, timeout)
                self.logger.info(f"ip: {device['ip']} {out} {err}")
                if err:
                    device_log += err
                    raise Exception(err)
                device_log += out
            except Exception as e:
                log_line = "ip: {} failed to execute <{}> due to execption: {}\nskipping this device".format(
                    device["ip"], cmd, str(e)
                )
                self.logger.error(log_line)
                result_dict["success"] = False
                result_dict["result"] = device_log + log_line
                try:
                    conn.close()
                except Exception as e:
                    self.logger.warning(f"error colsing connection: {e}")
                break
        result_dict["result"] = device_log
        result_dict["success"] = True
        json_result.append(result_dict)
        try:
            conn.close()
        except Exception as e:
            self.logger.warning(f"error colsing connection: {e}")
        return result_dict["success"]


class CommandHandler(ConfigHandler):
    def __init__(self, logger, command, group=None):
        """Used for ad-hoc commands.

        Args:
            logger (loguru.logger): logger instance.
            command (str): command(s) to execute. to use multiple commands separate them with &&.
            group ([str], optional): targets group name to execute on. Defaults to None.
        """
        self.group = group or "all"
        self.logger = logger
        parser_factory = ConfigParserFactory(content=self._prepare_content(command))
        self.config_parser = parser_factory.parser
        self.config_groups = self.config_parser.parse()

    def _prepare_content(self, command):
        result = f"[{self.group}:1]\n"
        for line in command.split("&&"):
            result += f"{line}\n"
        return result
