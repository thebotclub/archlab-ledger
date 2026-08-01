#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w161/pid
cd /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w161 && CUDA_VISIBLE_DEVICES=3 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
