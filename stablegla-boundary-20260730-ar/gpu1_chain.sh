#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w158/pid
echo $$ > /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w164/pid
cd /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w158 && CUDA_VISIBLE_DEVICES=1 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-boundary-20260730-ar/w164 && CUDA_VISIBLE_DEVICES=1 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
