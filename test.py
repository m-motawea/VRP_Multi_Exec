from lib.targets_parser import TargetParser
from lib.config_parser import ConfigParser
import json

with open("targets.ini", "r") as targets_file:
    text = "\n".join(targets_file.readlines())
    target_parser = TargetParser()
    target_groups = target_parser.parse(text)

print("target groups")
print(target_groups)
print("\n\n")

with open("config.ini", "r") as config_file:
    text = "\n".join(config_file.readlines())
    config_parser = ConfigParser()
    config_groups = config_parser.parse(text)
print("config_groups")
print(config_groups)
print("\n\n")

result = config_parser.order(config_groups)
print("ordered_groups")
print(result)
print("\n\n")


