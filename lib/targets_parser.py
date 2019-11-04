

class TargetParser(object):
    def __init__(self, *args):
        """
        :param args: pass the headers you need for the text
        """
        self.keys = args

    def parse(self, text):
        lines = text.split("\n")
        if not lines:
            return {}

        host_groups = {}
        current_group = None
        for i in range(0, len(lines)):
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
                    raise Exception("Error in line {}. Hosts must be grouped by headers".format(i))
                parsed_line = line.split()
                if len(parsed_line) < 3 or len(parsed_line) < 4:
                    raise Exception("Line {} is incorrect.".format(i))
                if len(parsed_line) == 3:
                    host_groups[current_group].append({
                        "ip": parsed_line[1],
                        "username": parsed_line[2],
                        "password": parsed_line[3]
                    })
                else:
                    host_groups[current_group].append({
                        "name": parsed_line[0],
                        "ip": parsed_line[1],
                        "username": parsed_line[2],
                        "password": parsed_line[3]
                    })
        result = {}
        if not self.keys:
            result = host_groups
        else:
            for key in self.keys:
                if host_groups.get(key):
                    result[key] = host_groups[key]
        return result

