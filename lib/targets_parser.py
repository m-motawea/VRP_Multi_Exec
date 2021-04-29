class TargetParser(object):
    def __init__(self, *args):
        """Parser for targets file."""
        self.keys = args

    def parse(self, text, password=None, key_filename=None):
        if password or key_filename:
            reduce_len = 1
        else:
            reduce_len = 0
        lines = text.splitlines()
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

        result = {}
        if not self.keys:
            result = host_groups
        else:
            for key in self.keys:
                if host_groups.get(key):
                    result[key] = host_groups[key]
        return result
