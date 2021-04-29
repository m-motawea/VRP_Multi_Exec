import yaml
import json
from .base import BaseParserFactory, BaseParser, ParserType


class TargetBaseParser(BaseParser):
    def filter_result(self, *keys):
        if not keys:
            return self.result
        else:
            result = {}
            for key in keys:
                if self.result.get(key):
                    result[key] = result[key]
        return result


class INIParser(TargetBaseParser):
    def parse(self, password=None, key_filename=None):
        if password or key_filename:
            reduce_len = 1
        else:
            reduce_len = 0
        lines = self.content.splitlines()
        if not lines:
            return {}

        host_groups = {}
        current_group = None
        for i, line in enumerate(lines):
            line = lines[i]
            if not line:
                continue

            if line[0] == "[" and line[-1] == "]":
                current_group = line[1:-1]
                if host_groups.get(current_group):
                    continue
                host_groups[current_group] = []
            else:
                if not current_group:
                    raise Exception(
                        "Error in line {}. Hosts must be grouped by headers".format(i)
                    )
                parsed_line = line.split()
                if (
                    len(parsed_line) < 3 - reduce_len
                    or len(parsed_line) > 4 - reduce_len
                ):
                    raise Exception("Line {} is incorrect.".format(i))
                if len(parsed_line) == 3 - reduce_len:
                    host_groups[current_group].append(
                        {
                            "ip": parsed_line[0],
                            "username": parsed_line[1],
                            "password": password
                            if password or key_filename
                            else parsed_line[2],
                            "key_filename": key_filename,
                        }
                    )
                elif len(parsed_line) == 4 - reduce_len:
                    host_groups[current_group].append(
                        {
                            "name": parsed_line[0],
                            "ip": parsed_line[1],
                            "username": parsed_line[2],
                            "password": password
                            if password or key_filename
                            else parsed_line[3],
                            "key_filename": key_filename,
                        }
                    )
                else:
                    raise Exception("Line {} is incorrect.".format(i))
        self.result = host_groups
        return self.result


class YAMLParser(TargetBaseParser):
    def parse(self, password=None, key_filename=None):
        self.result = yaml.safe_load(self.content)
        for group_devices in self.result.values():
            for value in group_devices:
                if not value.get("password"):
                    value["password"] = password
                if not value.get("key_filename"):
                    value["key_filename"] = key_filename
        return self.result


class JSONParser(TargetBaseParser):
    def parse(self, password=None, key_filename=None):
        self.result = json.loads(self.content)
        for group_devices in self.result.values():
            for value in group_devices:
                if not value.get("password"):
                    value["password"] = password
                if not value.get("key_filename"):
                    value["key_filename"] = key_filename
        return self.result


class TargetParserFactory(BaseParserFactory):
    PARSERS = {
        ParserType.INI: INIParser,
        ParserType.YAML: YAMLParser,
        ParserType.JSON: JSONParser,
    }
