import configparser


class VarParser(object):
    def __init__(self, vars_file_path):
        """parser for variables file

        Args:
            vars_file_path ([str]): path to the variables file
        """
        self.var_file_path = vars_file_path
        self.config = configparser.ConfigParser()
        self.config.read(vars_file_path)
        self.sections = self.config.sections()

    @staticmethod
    def get_variable_value(var):
        if len(var.split(",")) > 1:
            return var.split(",")
        else:
            return var

    def build_var_tree(self, target_groups):
        section_var_tree = {}
        group_vars = {}
        all_var = {}
        if "all" in self.config:
            # global variables
            for var in self.config["all"]:
                all_var[var] = self.get_variable_value(self.config["all"][var])

        for section in self.sections:
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
                    for var in self.config[section]:
                        section_var_tree[group][host][var] = self.get_variable_value(
                            self.config[section][var]
                        )
                else:
                    # group variables
                    section_var_tree[section] = {}
                    group_vars[section] = {}
                    for var in self.config[section]:
                        group_vars[section][var] = self.get_variable_value(
                            self.config[section][var]
                        )

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
