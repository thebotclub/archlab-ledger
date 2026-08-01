#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w156/pid
echo $$ > /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w162/pid
cd /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w156 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w162 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
