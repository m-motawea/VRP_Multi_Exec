from enum import Enum
import yaml
import json
from lib.logging import GlobalLogger
import re


class ParserType(Enum):
    YAML = "yaml"
    INI = "ini"
    JSON = "json"


class BaseParser:
    def __init__(self, content="") -> None:
        self.content = content
        self.result = None

    def parse(self):
        pass

    def filter_result(self, *keys, **kwargs):
        def check(item: dict):
            for key in keys:
                if key not in item:
                    return False
            for key, val in kwargs.items():
                if item.get(key) != val:
                    return False
            return True

        filtered_result = self.result
        if isinstance(self.result, list):
            filtered_result = []
            for item in self.result:
                if not isinstance(item, dict):
                    continue
                if not check(item):
                    continue
                filtered_result.append(item)
        elif isinstance(self.result, dict):
            if not check(self.result):
                filtered_result = {}
        
        return filtered_result


class BaseParserFactory:
    PARSERS = {
        ParserType.YAML: BaseParser, # class to create instance of
        ParserType.JSON: BaseParser,
        ParserType.INI: BaseParser,
    }
    def __init__(self, file_path="", content="") -> None:
        self.file_path = file_path
        self.content = content
        self.parser_type = None
        self._parser = None
        self.logger = GlobalLogger()

    
    @property
    def parser(self):
        if not self._parser:
            self.parser_type = self._get_parser_type(self.file_path, self.content)
            if self.parser_type not in self.PARSERS:
                raise Exception(f"no parser available for type: {self.parser_type}")
            self._parser = self.PARSERS[self.parser_type](self.content)
        return self._parser


    def _get_parser_type(self, file_path="", content=""):
        if all([file_path, content]) or not any([file_path, content]):
            raise Exception("must pass exactly one of file_path or content.")

        if file_path:
            return self._get_file_type(file_path)
        return self._get_content_type(content)
    

    def _get_file_type(self, file_path):
        with open(file_path, "r") as f:
            self.content = f.read()
        if file_path.endswith(".yaml") or file_path.endswith(".yml"):
            parser_type = ParserType.YAML
        elif file_path.endswith(".json"):
            parser_type = ParserType.JSON
        elif file_path.endswith(".ini"):
            parser_type = ParserType.INI
        else:
            self.logger.debug(f"can't identify file: {file_path} extension")
            self.logger.debug(f"attempting to identify file: {file_path} content type")
            parser_type = self._get_content_type(self.content)
        return parser_type

    def _get_content_type(self, content):
        try:
            json.loads(content)
            return ParserType.JSON
        except Exception as e:
            self.logger.debug(f"failed to load content as json due to error {e}")
        
        try:
            yaml.load(content)
            return ParserType.YAML
        except Exception as e:
            self.logger.debug(f"failed to load content as yaml due to error {e}")

        self.logger.debug("proceeding with default content type as ini")
        return ParserType.INI