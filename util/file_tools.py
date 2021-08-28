from abc import ABCMeta, abstractmethod

from typing import Dict, Optional, List
import re
import codecs
from collections import OrderedDict

import yaml

import xml.etree.ElementTree as XmlEt

from util.annot_datasets import VocXmlDataset, Bndbox, Size
from logging import getLogger, NullHandler

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class FileHandler(metaclass=ABCMeta):
    def __init__(self, encoding: str = 'utf-8'):
        self._codec = encoding

    @staticmethod
    def suffix_check(suffix_list: List[str], file_name: str) -> bool:
        suffix_list = [s.strip('.') for s in suffix_list]
        suffix = '|'.join(suffix_list).upper()
        pattern_str = r'\.(' + suffix + r')$'
        if not re.search(pattern_str, file_name.upper()):
            mes = f'''
            Suffix of the file name should be "{suffix}".
            Current file name ： {file_name}
            '''
            logger.error(mes)
            return False
        return True

    def read(self, file_name: str):
        try:
            with codecs.open(file_name, 'r', self._codec) as srw:
                return self.read_handling(srw)
        except FileNotFoundError:
            logger.error(f"{file_name} can not be found ...")
        except OSError as e:
            logger.error(f"OS error occurred trying to read {file_name}")
            logger.error(e)

    def write(self, data, file_name: str):
        try:
            with codecs.open(file_name, 'w', self._codec) as srw:
                self.write_handling(data, srw)
        except OSError as e:
            logger.error(f"OS error occurred trying to write {file_name}")
            logger.error(e)

    @abstractmethod
    def read_handling(self, srw: codecs.StreamReaderWriter):
        raise NotImplementedError

    @abstractmethod
    def write_handling(self, data, srw: codecs.StreamReaderWriter):
        raise NotImplementedError


class YamlHandler(FileHandler):
    def __init__(self, codec: str = 'utf-8'):
        super().__init__(codec)

    def read_handling(self, srw: codecs.StreamReaderWriter):
        return yaml.safe_load(srw)

    def write_handling(self, data, srw: codecs.StreamReaderWriter):
        yaml.safe_dump(data, srw, encoding=self._codec, allow_unicode=True, default_flow_style=False)


class TxtHandler(FileHandler):
    def __init__(self, codec: str = 'utf-8'):
        super().__init__(codec)

    def read_handling(self, srw: codecs.StreamReaderWriter) -> List[str]:
        line_list = []
        line = srw.readline()
        while line:
            line = line.rstrip()
            line_list.append(line)
            line = srw.readline()
        return line_list

    def write_handling(self, data: List[str], srw: codecs.StreamReaderWriter):
        data_cl = [s + '\n' for s in data]
        srw.writelines(data_cl)


class PbtxtAnalyzer(FileHandler):
    def __init__(self, codec: str = 'utf-8'):
        super().__init__(codec)

    def read_handling(self, srw: codecs.StreamReaderWriter):
        item_id = None
        item_name = None
        items = OrderedDict()

        for line in srw:
            line.replace(" ", "")
            if line == "item{":
                pass
            elif line == "}":
                pass
            elif "id" in line:
                item_id = int(line.split(":", 1)[1].strip())
            elif "name" in line:
                item_name = line.split(":", 1)[1].replace("'", "").strip()

            if item_id is not None and item_name is not None:
                items[item_name] = item_id
                item_id = None
                item_name = None

        return items

    def write_handling(self, data, srw: codecs.StreamReaderWriter):
        pass

    def parse(self, pbtxt_file: str) -> Optional[Dict]:
        # check the file suffix
        if not self.suffix_check(['.pbtxt'], pbtxt_file):
            return None

        return self.read(pbtxt_file)


class VocXmlAnalyzer(FileHandler):
    def __init__(self, codec: str = 'utf-8'):
        super().__init__(codec)

    def read_handling(self, srw: codecs.StreamReaderWriter):
        return XmlEt.parse(srw)

    def write_handling(self, data, srw: codecs.StreamReaderWriter):
        pass

    def parse(self, xml_file: str) -> Optional[VocXmlDataset]:
        # check the file suffix
        if not self.suffix_check(['.xml'], xml_file):
            return None

        et = self.read(xml_file)

        if et is None:
            return None

        root = et.getroot()

        # size
        xml_size = root.find('size')
        ntup_size = Size(
            int(xml_size.find("width").text),
            int(xml_size.find("height").text),
            int(xml_size.find("depth").text),
        )

        # objects
        xml_objects = root.findall('object')

        if len(xml_objects) == 0:
            return None

        objects_list = []

        for ob in xml_objects:
            name = ob.find('name').text
            xml_bndbox = ob.find('bndbox')
            ntup_bndbox = Bndbox(
                float(xml_bndbox.find('xmin').text),
                float(xml_bndbox.find('ymin').text),
                float(xml_bndbox.find('xmax').text),
                float(xml_bndbox.find('ymax').text),
            )
            # objects_list.append({name: ntup_bndbox})
            objects_list.append((name, ntup_bndbox))

        dataset = VocXmlDataset(
            size=ntup_size,
            objects=objects_list,
        )

        return dataset


if __name__ == "__main__":
    file = 'hansen.mp4#t=0.033333.xml'

    xa = VocXmlAnalyzer()

    data = xa.parse(file)

    print(data.size)

    objects = data.objects
    for d in objects:
        print(d)

    # yaml
    yh = YamlHandler()

    '''
    yaml ファイル内で、
        names: ['hoge', 'fuga' ]
    と
        names:
        - hoge
        - fuga
    は同義？
    '''
    dic_data = {
        'train': 'data/train/images',
        'val': 'data/valid/images',
        'nc': 2,
        'names': ['hoge', 'fuga'],
    }

    yh.write(dic_data, 'test.yaml')

    data = yh.read('test.yaml')
    print(data)

    # pbtxt
    file = 'pascal_label_map.pbtxt'
    pba = PbtxtAnalyzer()

    data = pba.parse(file)

    print(data)

    # txt
    str_list = [
        '1 0.334 0.645 0.162 0.244',
        '0 0.627 0.725 0.162 0.331',
    ]

    file = 'test.txt'
    thd = TxtHandler()

    thd.write(str_list, file)

    strs = thd.read(file)
    print(strs)
