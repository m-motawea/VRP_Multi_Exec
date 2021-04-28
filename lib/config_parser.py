class ConfigParser(object):
    @staticmethod
    def parse(text):
        lines = text.splitlines()
        if not lines:
            return {}

        config_groups = {}
        current_group = None
        for i in range(0, len(lines)):
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
        return config_groups

    @staticmethod
    def order(config_groups):
        groups = list(config_groups.keys())
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
                    "config": config_groups[order_dict[order]],
                    "type": "ordered",
                }
            )
        return result
