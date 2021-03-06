
# vott2yolo_cv

[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)

This script converts the Pascal-VOC format *.xml files output from VoTT ver2.* to the yolo format *.txt files.


Requires `Python` >= 3.7 

## Usage

Specify the directory output from VoTT (Pascal-VOC format) as the target.

The following is the structure of the target directory to be analyzed.
```
.
└── ****-PascalVOC-export
    ├── Annotations
    │   └── ****.xml
    ├── ImageSets
    ├── JPEGImages
    │   └── ****.jpg
    └── pascal_label_map.pbtxt
```

If the target directory is `I:\origin_data\hoge-PascalVOC-export` and the output destination is `yolo_out`, the example is as follows. 

```commandline
$ python vott2yolo_cv.py -t I:\origin_data\hoge-PascalVOC-export -o yolo_out
```

See help for more information on the options.

```commandline
$ python vott2yolo_cv.py -h
```





