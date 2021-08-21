
for seed in {0..4}
do
    for env in 'simple_crypto' 'simple_adversary' 'simple_tag' 'simple_push'
    do
        for gp in 'mmmaddpg'
        do
            for bp in 'maddpg' 'mmmmddpg'
            do
                echo "results/$env/$gp-$bp-'0'/$seed/"

                    python experiments/train.py \
                    --scenario $env \
                    --seed $seed \
                    --num-adversaries 1 \
                    --good-policy $gp \
                    --bad-policy $bp \
                    --average_perf_wt 0 \
                    --lr 0.001 \
                    --adv-eps 0.001 \
                    --adv-eps-s 0.001 \
                    --plots-dir results/$env/$gp-$bp-'0'/$seed/ \
                    --exp-name run &

                echo " "

                for sp in 10 100
                do
                    for sm in 0.5 1.0
                    do
                        echo "results/$env/$gp-$bp-$sm-$sp/$seed/"

                        python experiments/train.py \
                        --scenario $env \
                        --seed $seed \
                        --num-adversaries 1 \
                        --good-policy $gp \
                        --bad-policy $bp \
                        --average_perf_wt $sm \
                        --lr 0.001 \
                        --num_samples $sp \
                        --adv-eps 0.001 \
                        --adv-eps-s 0.001 \
                        --plots-dir results/$env/$gp-$bp-$sm-$sp/$seed/ \
                        --exp-name run &

                        echo " "
                    done

                    echo "results/$env/$gp-$bp-$sp-'k-min'/$seed/"

                    python experiments/train.py \
                    --scenario $env \
                    --seed $seed \
                    --num-adversaries 1 \
                    --good-policy $gp \
                    --bad-policy $bp \
                    --average_perf_wt 1.0 \
                    --lr 0.001 \
                    --num_samples $sp \
                    --adv-eps 0.001 \
                    --adv-eps-s 0.001 \
                    --plots-dir results/$env/$gp-$bp-$sp-'k-min'/$seed/ \
                    --k_minima \
                    --exp-name run

                    echo " "

                done
            done
        done
        
        echo results/$env/'maddpg'-'maddpg'/$seed/

        python experiments/train.py \
        --scenario $env \
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
