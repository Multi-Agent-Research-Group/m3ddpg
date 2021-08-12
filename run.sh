
for seed in {0..9}
do
    for env in 'simple' 'simple_adversary' 'simple_tag' 'simple_push'
    do
        for adv in {0..1}
        do
            python experiments/train.py --num-episodes 100000 --num-adversaries $adv --scenario $env --exp-name 'new_'$env'_seed'$seed'_adv'$adv --seed $seed --plots-dir results1/ &
            python experiments/train.py --num-episodes 100000 --num-adversaries $adv --scenario $env --exp-name 'new_avg_'$env'_seed'$seed'_adv'$adv --seed $seed --plots-dir results1/ --num_samples 20 --average_perf_wt 0.5 &
        done
    done
done