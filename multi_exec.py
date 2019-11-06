from lib.handlers.device_config_handler import ConfigHandler
from lib.targets_parser import TargetParser
from lib.var_parser import VarParser
import argparse
import json

argparser = argparse.ArgumentParser(prog="multi_exec", description="configure VRP devices")
argparser.add_argument("-t", "--targets", help="path to targets file", required=True)
argparser.add_argument("-c", "--config", help="path to configuration file")
argparser.add_argument("-v", "--vars", help="target variables")
argparser.add_argument("-m", "--module", help="module name")
argparser.add_argument("-a", "--args", help="module arguments")
argparser.add_argument("-o", "--output", help="log file location")

args = argparser.parse_args()
targets_file = args.targets
config_file = args.config
vars_file = args.vars
module_name = args.module
module_args = args.args
log_file_path = args.output



def get_target_groups(targets_path):
    with open(targets_path) as targets_file:
        targets_text = "\n".join(targets_file.readlines())
    target_parser = TargetParser()
    target_groups = target_parser.parse(targets_text)
    return target_groups

def get_complete_variables(variables_path, target_groups):
    var_parser = VarParser(variables_path)
    var_tree = var_parser.build_var_tree(target_groups)
    return var_tree

def main():
    if not module_name and not config_file:
        print("you must specify either a module or a config file.")
        exit(0)

    if module_name and config_file:
        print("you can't use both config and module at the same time.")
        exit(0)

    target_groups = get_target_groups(targets_file)
    var_tree = get_complete_variables(vars_file, target_groups)
    #print("target_groups")
    #print(target_groups)
    #print("\n\n")
    if config_file:
        handler = ConfigHandler(config_file)
        result = handler.execute_config(target_groups, out_file=log_file_path)
        with open("multi_exec.json", "w") as result_json:
            json.dump(result, result_json, indent=4)
    else:
        print("modules are not implemented yet.")
        exit(0)



if __name__ == "__main__":
    main()
