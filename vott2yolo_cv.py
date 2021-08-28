from pathlib import Path
from typing import List, Dict, Tuple, Optional
import argparse

from logging import getLogger, DEBUG, basicConfig

basicConfig(level=DEBUG)

logger = getLogger(__name__)
logger.setLevel(DEBUG)

from util.file_tools import VocXmlAnalyzer, PbtxtAnalyzer, YamlHandler, TxtHandler
from util.path_tools import GetFileListBySuffix, OutputFilePathGenerator
from util.annot_datasets import Bndbox, Size


class Voc2Yolo(object):
    def __init__(self, out_dir: str = './yolo_out/', yaml_name: str = 'data'):
        self._out_dir = out_dir
        self._yaml_file_stem = yaml_name
        self._class_list = None

        # utilities
        self._pbtxt_ana = PbtxtAnalyzer()
        self._xml_ana = VocXmlAnalyzer()
        self._yaml_hd = YamlHandler()
        self._txt_hd = TxtHandler()
        self._xml_file_picker = GetFileListBySuffix(file_suffix='.xml')
        self._txt_file_path_gen = OutputFilePathGenerator(
            out_suffix='.txt',
            output_dir=str(Path(self._out_dir) / 'labels'),
        )

    @staticmethod
    def coordinate2yolo(size: Size, box: Bndbox) -> Tuple[float, float, float, float]:
        dw = 1. / size.width
        dh = 1. / size.height

        x_cen = ((box.xmin + box.xmax) / 2.0) * dw
        y_cen = ((box.ymin + box.ymax) / 2.0) * dh
        w = (box.xmax - box.xmin) * dw
        h = (box.ymax - box.ymin) * dh

        return round(x_cen, 3), round(y_cen, 3), round(w, 3), round(h, 3)

    @staticmethod
    def dict_for_yolo_yaml(dir_name: str, class_list: List[str]) -> Optional[Dict]:
        if class_list is None:
            return None
        dict_for_yaml = {
            'train': f'{dir_name}/train/images',
            'val': f'{dir_name}/valid/images',
            'nc': len(class_list),
            'names': class_list
        }
        return dict_for_yaml

    def parse_pbtxt(self, pbtxt_path: str) -> List[str]:
        pb_data = self._pbtxt_ana.parse(pbtxt_path)
        return list(pb_data.keys())

    def convert_xml_files(self, xml_dir: str):
        xml_file_list = self._xml_file_picker(xml_dir)
        for f in xml_file_list:
            ds = self._xml_ana.parse(f)
            size = ds.size
            print_list = []
            for name, box in ds.objects:
                name_id = self._class_list.index(name)
                coord = self.coordinate2yolo(size, box)
                coord = (name_id,) + coord
                print_list.append(" ".join(str(x) for x in coord))

            txt_file_path = self._txt_file_path_gen(f)
            self._txt_hd.write(print_list, txt_file_path)

    def parse(self, annot_dir: str, pbtxt_path: str):
        self._class_list = self.parse_pbtxt(pbtxt_path)
        assert self._class_list is not None, "Probably failed to parse the pttxt file."
        d_yaml = self.dict_for_yolo_yaml(self._yaml_file_stem, self._class_list)
        p_out_dir = Path(self._out_dir)
        p_yaml_file = p_out_dir / Path(self._yaml_file_stem + '.yaml')
        self._yaml_hd.write(d_yaml, str(p_yaml_file))
        self.convert_xml_files(annot_dir)


def parse_option():
    k_TARGET_DIR = './PascalVOC-export'
    k_OUT_DIR = './yolo_out'
    k_YAML_NAME = 'data'

    dc = """
        This script converts the Pascal-VOC format *.xml files output from VoTT ver2.* to the yolo format *.txt files .
    """
    parser = argparse.ArgumentParser(description=dc)

    parser.add_argument('-t', '--target_dir', type=str, dest='target_dir', default=k_TARGET_DIR,
                        help=f"""
                        Specify the directory of the Pascal-VOC format output by VoTT ver2.* 
                        as the target of this script.
                        e.g. {k_TARGET_DIR}
                        """
                        )
    parser.add_argument('-o', '--output_dir', type=str, dest='out_dir', default=k_OUT_DIR,
                        help=f"Specify the output directory of converted yolo *.txt files. e.g. {k_OUT_DIR}")
    parser.add_argument('-y', '--yaml_name', type=str, dest='yaml_name', default=k_YAML_NAME,
                        help=f"Specify the name (stem only) of the output yaml file. e.g. {k_YAML_NAME}")
    parser.add_argument('--xml_annot_dir', type=str, dest='annot_dir', default=None,
                        help=f"Specify the reference *.xml files directory if you need.")
    parser.add_argument('--pbtxt_file', type=str, dest='pbtxt_file', default=None,
                        help=f"Specify the reference *.pbtxt file if you need.")

    return parser.parse_args()


def main():
    k_XML_ANNOT_DIR = 'Annotations'
    k_PBTXT_FILE = 'pascal_label_map.pbtxt'

    args = parse_option()
    target_dir = args.target_dir
    out_dir = args.out_dir
    yaml_name = args.yaml_name
    annot_dir = args.annot_dir
    pbtxt_file = args.pbtxt_file

    try:
        p_target_dir = Path(target_dir)
        if not p_target_dir.exists():
            raise FileNotFoundError(
                f"""
                No such file or directory. -> {target_dir}"
                Specify the directory of the Pascal-VOC format output by VoTT ver2.* 
                as the target of this script.
                """
            )
        f_y = p_target_dir.glob(k_PBTXT_FILE)
        d_y = p_target_dir.glob(k_XML_ANNOT_DIR)

        pbtxt_file = str(next(f_y)) if pbtxt_file is None else pbtxt_file
        annot_dir = str(next(d_y)) if annot_dir is None else annot_dir

        p_out_dir = Path(out_dir)
        if not p_out_dir.exists():
            raise FileNotFoundError(
                f"""
                No such file or directory. -> {out_dir}"
                Before running this script, please create an output directory!
                """
            )

        logger.info(f"  Current target is '{target_dir}', then ...")
        logger.info(f" '{annot_dir}' was set as xml annotation directory.")
        logger.info(f" '{pbtxt_file}' was set as pbtxt file.")
        logger.info(f" '{out_dir}' was set as ouput directory.")
        logger.info(f" '{yaml_name}' was set as yaml file name stem.")

        v2y = Voc2Yolo(out_dir, yaml_name)
        v2y.parse(annot_dir, pbtxt_file)

    except FileNotFoundError as e:
        logger.error(e)
    except OSError as e:
        logger.error(e)


if __name__ == "__main__":
    main()
