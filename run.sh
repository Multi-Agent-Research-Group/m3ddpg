
for seed in {0..9}
do
    for env in 'simple' 'simple_adversary' 'simple_tag' 'simple_push'
    do
        for adv in {0..1}
        do
            python experiments/train.py --num-episodes 100000 --num-adversaries $adv --scenario $env --exp-name $env'_'$seed'_'$adv --seed $seed --plots-dir results/ &
            python experiments/train.py --num-episodes 100000 --num-adversaries $adv --scenario $env --exp-name 'avg_'$env'_'$seed'_'$adv --seed $seed --plots-dir results/ --num_samples 5 --average_perf_wt 0.5 &
        done
    done
done