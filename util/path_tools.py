from typing import List, Union

from pathlib import Path

from abc import ABCMeta, abstractmethod


class PathHandler(metaclass=ABCMeta):
    @abstractmethod
    def __call__(self, **kwargs):
        pass

    @staticmethod
    def dir_path_obj(dir_path: str) -> Path:
        assert dir_path, "Need to specify the directory path. It is currently empty."
        p_dir = Path(dir_path)
        assert p_dir.is_dir(), f"The directory '{str(p_dir)}' does not exist !"
        return p_dir

    @staticmethod
    def file_path_obj(file_path: str) -> Path:
        assert file_path, "Need to specify the file path. It is currently empty."
        p_file = Path(file_path)
        assert p_file.is_file(), f"The file '{str(p_file)}' does not exist!"
        return p_file


class GetFileListBySuffix(PathHandler):
    def __init__(self, file_suffix: Union[str, List[str]], recursive: bool = False):
        """
        This class is for getting file list with specified suffix.

        Parameters
        ----------
        file_suffix : Specify the suffix of the files to search.
        recursive : Whether to search recursively or not.
        """

        assert file_suffix, "Need to specify the file extension. It is currently empty."
        self._recursive = recursive

        self._file_suffix_list = []
        if type(file_suffix) is str:
            self._file_suffix_list.append(file_suffix)
        if type(file_suffix) is list:
            self._file_suffix_list = file_suffix

    def __call__(self, src_dir: str = None) -> List[str]:
        file_names = []
        p_src_dir = Path.cwd() if src_dir is None else self.dir_path_obj(src_dir)

        for suffix in self._file_suffix_list:
            wild_card = "*" + suffix
            if self._recursive:  # for recursive search
                wild_card = "**/" + wild_card
            p_file = [p for p in p_src_dir.glob(wild_card)]
            p_file_str = [str(p.resolve()) for p in p_file]
            file_names.extend(p_file_str)
        return file_names


class OutputFilePathGenerator(PathHandler):
    def __init__(self, out_suffix: str, output_dir: str = None, add_stem: str = None):
        """
        This class is is for generating a new file path.
        The new file path to be generated is based on the input file path,
        with the specified output directory and suffix.

        Parameters
        ----------
        out_suffix : The suffix of the file path to be generated.
        output_dir : The output directory path of the file path to be generated.
        add_stem : Strings to be added to the generated file path.
        """
        self._output_suffix = out_suffix
        self._add_stem = add_stem
        self._output_dir = output_dir

    def __call__(self, input_file_path: str, output_dir=None, add_stem: str = None):
        assert self._output_suffix, 'Specify the suffix of the output file!'
        assert self._output_dir, 'Specify the output directory path!'

        p_file = self.file_path_obj(input_file_path)

        # If the specified directory does not exist, create it.
        p_out_dir = Path(self._output_dir)
        if not p_out_dir.exists():
            p_out_dir.mkdir()

        p_tmp_file = p_file.with_suffix(self._output_suffix)

        add_stem = (self._add_stem or "") + (add_stem or "")  # If 'None', make it a string.
        if add_stem:
            out_file_name = p_tmp_file.stem + add_stem + p_tmp_file.suffix
        else:
            out_file_name = p_tmp_file.name

        # if p_file == p_tmp_file:  # When the file paths match.
        #     out_file_name = '_' + out_file_name

        p_out_file = p_out_dir.joinpath(out_file_name)

        return str(p_out_file.resolve())



