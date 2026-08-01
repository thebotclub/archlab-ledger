#!/bin/bash
echo $$ > /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/core_gpu3/pid
echo $$ > /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/tokenmatched/pid
cd /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/core_gpu3 && CUDA_VISIBLE_DEVICES=3 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
cd /home/hani/archlab-runs/stablegla-foxpro-transformer-claim-20260730-aq/tokenmatched && CUDA_VISIBLE_DEVICES=3 /home/hani/archlab/.venv/bin/python run.py > run.log 2>&1
