from vrp_multi_exec.lib.parsers.base import BaseParserFactory, BaseParser, ParserType
import json
import yaml
import configparser
import io
from collections import defaultdict


class BaseVarParser(BaseParser):
    @staticmethod
    def _merge_vars(target_groups, section_var_tree, group_vars, all_var):
        # add all hosts under a group to the var tree
        for target_group in target_groups:
            if not group_vars.get(target_group):
                group_vars[target_group] = {}
                if not section_var_tree.get(target_group):
                    section_var_tree[target_group] = {}
            for host_dict in target_groups[target_group]:
                if not section_var_tree[target_group].get(host_dict["ip"]):
                    section_var_tree[target_group][host_dict["ip"]] = {}

        for group in group_vars:
            # merge global variables to groups:
            for var in all_var:
                if group_vars[group].get(var):
                    continue
                else:
                    group_vars[group][var] = all_var[var]

            if section_var_tree.get(group):
                # merge group variables to hosts
                for host in section_var_tree[group]:
                    for var in group_vars[group]:
                        if section_var_tree[group][host].get(var):
                            continue
                        else:
                            section_var_tree[group][host][var] = group_vars[group][var]

        return section_var_tree


class INIParser(BaseVarParser):
    def parse(self, target_groups):
        def get_variable_value(var):
            if len(var.split(",")) > 1:
                return var.split(",")
            else:
                return var
        buf = io.StringIO(self.content)
        config = configparser.ConfigParser()
        config.read_file(buf)
        sections = config.sections()

        section_var_tree = {}
        group_vars = {}
        all_var = {}
        if "all" in config:
            # global variables
            for var in config["all"]:
                all_var[var] = get_variable_value(config["all"][var])

        for section in sections:
            if section == "all":
                continue

            if not section_var_tree.get(section):
                if ":" in section:
                    group = section.split(":")[0]
                    host = section.split(":")[1]
                    if not section_var_tree.get(group):
                        section_var_tree[group] = {}
                    section_var_tree[group][host] = {}
                    # device specific variables
                    for var in config[section]:
                        section_var_tree[group][host][var] = get_variable_value(
                            config[section][var]
                        )
                else:
                    # group variables
                    section_var_tree[section] = {}
                    group_vars[section] = {}
                    for var in config[section]:
                        group_vars[section][var] = get_variable_value(
                            config[section][var]
                        )

        self.result = self._merge_vars(target_groups, section_var_tree, group_vars, all_var)
        return self.result


class BaseSerializableParser(BaseVarParser):
    def _build_var_tree(self, parsed_content, target_groups):
        result = {}
        section_var_tree = defaultdict(lambda: defaultdict(dict))
        group_vars = {}
        for target_group, hosts in target_groups.items():
            result[target_group] = {}
            for host in hosts:
                result[target_group][host["ip"]] = {}
        
        all_var = parsed_content.get("all", {}).get("vars", {})
        for group, group_val in parsed_content.items():
            if group == "all":
                continue
            if group not in result:
                continue
            group_vars[group] = group_val.get("vars", {})
            for host in group_val:
                if host == "vars":
                    continue
                section_var_tree[group][host] = group_val[host].get("vars", {})

        self.result = self._merge_vars(target_groups, section_var_tree, group_vars, all_var)
        return self.result



class YAMLParser(BaseSerializableParser):
    def parse(self, target_groups):
        parsed_content = yaml.safe_load(self.content)
        self.result = self._build_var_tree(parsed_content, target_groups)
        return self.result


class JSONParser(BaseSerializableParser):
    def parse(self, target_groups):
        parsed_content = json.loads(self.content)
        self.result = self._build_var_tree(parsed_content, target_groups)
        return self.result


class VarParserFactory(BaseParserFactory):
    PARSERS = {
        ParserType.INI: INIParser,
        ParserType.YAML: YAMLParser,
        ParserType.JSON: JSONParser,
    }

