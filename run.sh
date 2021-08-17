
for seed in {0..4}
do
    for env in 'simple_crypto' 'simple_adversary' 'simple_tag' 'simple_push'
    do
        for gp in 'mmmaddpg'
        do
            for bp in 'maddpg' 'mmmmddpg'
            do
                for sm in 0 0.5 1.0
                do
                    echo "results/$env/$gp-$bp-$sm/$seed/"

                    python experiments/train.py \
                    --scenario $env \
                    --max-episode-len 50 \
                    --num_units 256 \
                    --seed $seed \
                    --num-adversaries 1 \
                    --good-policy $gp \
                    --bad-policy $bp \
                    --average_perf_wt $sm \
                    --lr 0.001 \
                    --adv-eps 0.001 \
                    --adv-eps-s 0.001 \
                    --plots-dir results/$env/$gp-$bp-$sm/$seed/ \
                    --exp-name run &

                    echo " "
                done
                    echo "results/$env/$gp-$bp-$sm/$seed/"

                    python experiments/train.py \
                    --scenario $env \
                    --max-episode-len 50 \
                    --num_units 256 \
                    --seed $seed \
                    --num-adversaries 1 \
                    --good-policy $gp \
                    --bad-policy $bp \
                    --average_perf_wt 1.0 \
                    --lr 0.001 \
                    --adv-eps 0.001 \
                    --adv-eps-s 0.001 \
                    --plots-dir results/$env/$gp-$bp-'k-min'/$seed/ \
                    --k_minima \
                    --exp-name run &

                    echo " "
            done
        done
            echo results/$env/'maddpg'-'maddpg'/$seed/

            python experiments/train.py \
            --scenario $env \
            --max-episode-len 50 \
            --num_units 256 \
            --seed $seed \
            --num-adversaries 1 \
            --lr 0.001 \
            --adv-eps 0.001 \
            --adv-eps-s 0.001 \
            --plots-dir results/$env/'maddpg'-'maddpg'/$seed/ \
            --exp-name run &

            echo " "
    done
    wait
done