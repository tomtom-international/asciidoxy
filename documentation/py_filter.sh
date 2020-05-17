#!/bin/bash
doxypypy -a -c $1 | sed 's/#        /# /'
