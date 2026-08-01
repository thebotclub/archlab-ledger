#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-transformer-lr-audit-20260730-as/s1_lr5em4/pid
echo $$ > /home/hani/archlab-runs/stablegla-transformer-lr-audit-20260730-as/s2_lr5em4/pid
echo $$ > /home/hani/archlab-runs/stablegla-transformer-lr-audit-20260730-as/s3_lr3em4/pid
cd /home/hani/archlab-runs/stablegla-transformer-lr-audit-20260730-as/s1_lr5em4 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-transformer-lr-audit-20260730-as/s2_lr5em4 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-transformer-lr-audit-20260730-as/s3_lr3em4 && CUDA_VISIBLE_DEVICES=0 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
