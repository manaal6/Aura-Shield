"""python -m experiments.kaust_three_pillars.run_all — runs every pillar end-to-end."""
from .runners import (run_adaptive, run_constitution, run_dpo,
                      run_integrated_eval, run_unlearning)

if __name__ == "__main__":
    run_constitution()
    run_adaptive()
    run_dpo()
    run_unlearning()
    run_integrated_eval()
    print("ALL KAUST PILLAR EXPERIMENTS COMPLETE — see results/kaust_three_pillars/")
