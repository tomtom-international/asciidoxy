#!/bin/bash
python doxypypy.py -a -c $1 | sed 's/#        /# /'
