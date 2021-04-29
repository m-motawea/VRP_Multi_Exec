import yaml
import json
from vrp_multi_exec.lib.parsers.base import BaseParserFactory, BaseParser, ParserType


class INIParser(BaseParser):
    def parse(self):
        lines = self.content.splitlines()
        if not lines:
            return {}

        config_groups = {}
        current_group = None
        for i, line in enumerate(lines):
            line = lines[i]
            if not line:
                continue

            if line[0] == "[" and line[-1] == "]":
                current_group = line[1:-1]
                if config_groups.get(current_group):
                    continue
                config_groups[current_group] = []
            else:
                if not current_group:
                    raise Exception(
                        "Error in line {}. Hosts must be grouped by headers".format(i)
                    )
                config_groups[current_group].append(line)
        self.result = config_groups
        return self.result

    def order(self):
        groups = list(self.result.keys())
        result = []
        order_dict = {}
        for group_name in groups:
            if ":" not in group_name:
                raise Exception("no order found for group: {}".format(group_name))
            else:
                parsed_name = group_name.split(":")
                if len(parsed_name) > 2:
                    raise Exception("invalid group name: {}.".format(group_name))
                group_order = int(parsed_name[1])
                if order_dict.get(group_order):
                    raise Exception(
                        "order {} in group {} was already used for group {}.".format(
                            group_order, group_name, order_dict[group_order]
                        )
                    )
                order_dict[group_order] = group_name

        for order in sorted(order_dict.keys()):
            result.append(
                {
                    "name": order_dict[order],
                    "config": self.result[order_dict[order]],
                    "type": "ordered",
                }
            )
        return result


class YAMLParser(BaseParser):
    def __init__(self, content) -> None:
        super().__init__(content=content)
        self.ordered_result = []

    def parse(self):
        self.ordered_result = yaml.safe_load(self.content)
        self.result = {}
        for i, item in enumerate(self.ordered_result):
            item["name"] = f"{item['group']}:{i}"
            item["config"] = item["config"].splitlines()
            self.result[item["name"]] = item["config"]
        return self.result

    def order(self):
        return self.ordered_result


class JSONParser(BaseParser):
    def __init__(self, content) -> None:
        super().__init__(content=content)
        self.ordered_result = []

    def parse(self):
        self.ordered_result = json.loads(self.content)
        self.result = {}
        for i, item in enumerate(self.ordered_result):
            item["name"] = f"{item['group']}:{i}"
            item["config"] = item["config"].splitlines()
            self.result[item["name"]] = item["config"]
        return self.result

    def order(self):
        return self.ordered_result


class ConfigParserFactory(BaseParserFactory):
    PARSERS = {
        ParserType.INI: INIParser,
        ParserType.YAML: YAMLParser,
        ParserType.JSON: JSONParser,
    }
