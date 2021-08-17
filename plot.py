import argparse
import itertools
import os
import pathlib
import pickle
import time

import matplotlib as mpl
from matplotlib import gridspec
from matplotlib import lines
import matplotlib.pyplot as plt
import numpy as np
import pickle


def smooth(vals, window):
    '''Smooths values using a sliding window.'''

    if window > 1:
        if window > len(vals):
            window = len(vals)
        y = np.ones(window)
        x = vals
        z = np.ones(len(vals))
        mode = 'same'
        vals = np.convolve(x, y, mode) / np.convolve(z, y, mode)

    return vals


def stats(xs, means, stds):
    '''Extract statistics over the common range of x values.'''

    # Extract the common range of x values.
    lengths = [len(x) for x in xs]
    min_length = min(lengths)
    xs = [x[:min_length] for x in xs]
    assert len(xs) == 1 or np.all(xs[1:] == xs[0]), xs
    x = xs[0]

    # Compute statistics.
    means = np.array([mean[:min_length] for mean in means])
    mean = means.mean(axis=0)
    min_mean = means.min(axis=0)
    max_mean = means.max(axis=0)
    if stds is not None:
        stds = np.array([std[:min_length] for std in stds])
        variances = stds ** 2
        var_within = variances.mean(axis=0)
        var_between = ((means - mean) ** 2).mean(axis=0)
        std = np.sqrt(var_within + var_between)
    else:
        std = None

    return x, mean, min_mean, max_mean, std


def flip(items, columns):
    '''Flips values to fill horizontally the legend instead of vertically.'''

    return itertools.chain(*[items[i::columns] for i in range(columns)])


def get_data(
    paths, y_axis, x_min, x_max, window, num_adv
):
    '''Gets data from the paths and benchmark.'''

    data = {}

    # List the log files in paths.
    log_paths = []
    for path in paths:
        if os.path.isdir(path):
            log_paths.extend(pathlib.Path(path).rglob('run_*'))
        elif path[-7:-3] == 'run_':
            log_paths.append(path)

    # Load the data from the log files.
    for path in log_paths:
        path = str(path)
        sub_path, file = os.path.split(path)
        dfs = {}

        if file == 'run_agrewards.pkl':
            # Extract the environment, agent and seed from the paths.
            env, agent, seed = sub_path.split(os.sep)[-3:]

            # Load the data.
            agent_rew, ep_rew = None, None
            with open(path, 'rb') as fp:
                agent_rew = np.array(pickle.load(fp))
            
            with open(sub_path+"/run_rewards.pkl", 'rb') as fp:
                ep_rew = np.array(pickle.load(fp))
            
            num_agents = agent_rew.shape[0]//ep_rew.shape[0]
            df_seed = np.reshape(agent_rew, (ep_rew.shape[0], num_agents))
            
            x = np.arange(len(df_seed))
            # The x axis should be sorted.
            if not np.all(np.diff(x) > 0):
                print('Skipping unsorted {} {} {}'.format(env, agent, seed))
                continue
            if x_min and x[-1] < x_min:
                print('Skipping {} {} {} ({} steps)'.format(env, agent, seed, x[-1]))
                continue
            dfs[seed] = df_seed

        for seed, df in dfs.items():
            if env not in data:
                data[env] = {}
            if agent not in data[env]:
                data[env][agent] = {}
            assert seed not in data[env][agent]

            # Extract the data.
            x = np.arange(len(df))
            df = np.array(df)
            std = None
            if y_axis == 'episode_score':
                mean =  np.sum(df, axis=1)
            elif y_axis == 'agent_score':
                mean = np.mean(df[:,num_adv:], axis=1)
                std = np.std(df[:,num_adv:], axis=1)
            elif y_axis == 'adversary_score':
                mean = np.mean(df[:,:num_adv], axis=1)
                std = np.std(df[:,:num_adv], axis=1)
            else:
                raise KeyError('Key {} not found.'.format(y_axis))

            # Limit the range of x values and smooth.
            if x_max:
                max_index = np.argmax(x > x_max) or len(x)
            else:
                max_index = len(x)
            x = x[:max_index]
            mean = smooth(mean, window)
            mean = mean[:max_index]
            if std is not None:
                std = smooth(std, window)
                std = std[:max_index]

            data[env][agent][seed] = x, mean, std

    # Aggregate the runs and compute the statistics.
    for env, env_data in data.items():
        for agent, agent_data in env_data.items():
            xs, means, stds = [], [], []
            for seed, (x, mean, std) in agent_data.items():
                xs.append(x)
                means.append(mean)
                stds.append(std)
            if stds[0] is None:
                stds = None
            print(env, agent)
            env_data[agent] = dict(
                seeds=(xs, means), stats=stats(xs, means, stds))
    
    return data


def plot(
    paths, y_axis, x_label, y_label, window, interval, show_seeds,
    columns, x_min, x_max, name, save_formats, num_adv,
    cmap, legend_columns, legend_marker_size, dpi, fig
):
    '''Plots results from experiments and benchmark data.'''

    # Extract the data.
    print('Loading data...')
    data = get_data(
        paths, y_axis, x_min, x_max, window, num_adv)

    # List the environments.
    envs = sorted(data.keys(), key=str.casefold)
    num_envs = len(envs)
    if num_envs == 0:
        print('No logs found.')
        return

    # List the agents.
    agents = set()
    for env in data:
        for agent in data[env]:
            agents.add(agent)
    agents = sorted(agents, key=str.casefold)
    num_agents = len(agents)

    if not cmap:
        if num_agents <= 10:
            cmap = 'tab10'
        elif num_agents <= 20:
            cmap = 'tab20'
        else:
            cmap = 'rainbow'
    cmap = plt.get_cmap(cmap)

    if isinstance(cmap, mpl.colors.ListedColormap):
        colors = cmap(range(num_agents))
    else:
        colors = list(cmap(np.linspace(0, 1, num_agents)))

    agent_colors = {a: c for a, c in zip(agents, colors)}
    if columns is None:
        columns = int(np.ceil(np.sqrt(num_envs)))
    else:
        columns = min(columns, num_envs)
    rows = int(np.ceil(num_envs / columns))
    if fig is None:
        plt.ion()
        fig = plt.figure(figsize=(columns * 6, rows * 5))
    else:
        fig.clear()
    grid = gridspec.GridSpec(
        rows + 1, 1 + columns, height_ratios=[1] * rows + [0.1],
        width_ratios=[0] + [1] * columns)
    axes = []
    for i in range(num_envs):
        ax = fig.add_subplot(grid[i // columns, 1 + i % columns])
        axes.append(ax)

    print('Plotting...')
    for env, ax in zip(envs, axes):
        # Plot intervals first.
        if interval in ['std', 'bounds']:
            for agent in sorted(data[env], key=str.casefold):
                color = agent_colors[agent]
                x, mean, min_mean, max_mean, std = data[env][agent]['stats']
                if interval == 'std':
                    if std is None:
                        print('No std found in the data.')
                    else:
                        ax.fill_between(
                            x, mean - std, mean + std, color=color, alpha=0.1,
                            lw=0)
                elif interval == 'bounds':
                    ax.fill_between(
                        x, min_mean, max_mean, color=color, alpha=0.1, lw=0)

        # Plot means after.
        for agent in sorted(data[env], key=str.casefold):
            color = agent_colors[agent]

            # Plot each run if needed.
            xs, means = data[env][agent]['seeds']
            if show_seeds and len(xs) > 1:
                for x, mean in zip(xs, means):
                    ax.plot(x, mean, c=color, lw=1, alpha=0.5)

            # Plot the overall mean.
            x, mean = data[env][agent]['stats'][:2]
            ax.plot(x, mean, c=color, lw=2, alpha=1)

        # Finalize the figures.
        ax.locator_params(axis='x', nbins=6)
        ax.locator_params(axis='y', tight=True, nbins=6)
        ax.get_yaxis().set_major_formatter(
            mpl.ticker.FuncFormatter(lambda x, p: '{}'.format(x)))
        low, high = ax.get_xlim()
        if max(abs(low), abs(high)) >= 1e3:
            ax.ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
        ax.xaxis.grid(linewidth=0.5, alpha=0.5)
        ax.yaxis.grid(linewidth=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='both', which='both', length=0)
        x_label = 'Steps'
        if y_label is None:
            y_label = 'Score' if y_axis == 'episode_score' else y_axis
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(env)

    # Add a legend bellow.
    legend_ax = fig.add_subplot(grid[-1:, :])
    legend_ax.set_axis_off()
    handles = []
    for color in colors:
        marker = lines.Line2D(
            range(1), range(1), marker='o', markerfacecolor=color,
            markersize=legend_marker_size, linewidth=0, markeredgewidth=0)
        handles.append(marker)

    # Find a nice number of legend columns. Labels should not overlap.
    if legend_columns is None:
        legend_columns = range(num_agents, 0, -1)
    else:
        legend_columns = [legend_columns]
    for ncol in legend_columns:
        legend = legend_ax.legend(
            flip(handles, ncol), flip(agents, ncol), loc='center',
            mode='expand', borderaxespad=0, borderpad=0, handlelength=0.9,
            ncol=ncol, numpoints=1)
        legend_frame = legend.get_frame()
        legend_frame.set_linewidth(0)
        fig.tight_layout(pad=0, w_pad=0, h_pad=1.0)
        fig.canvas.draw()
        renderer = legend_ax.get_renderer_cache()
        h_packer = legend.get_children()[0].get_children()[1]
        target_width = h_packer.get_extent(renderer)[0]
        current_width = sum(
            [ch.get_extent(renderer)[0] for ch in h_packer.get_children()])
        if target_width > 1.3 * current_width:
            break

    # Save the plot in different formats if needed.
    if save_formats:
        print('Saving...')
        if name is None:
            if len(envs) > 1:
                name = 'results'
            else:
                name = envs[0]
        for save_format in save_formats:
            file_name = name + '.' + save_format
            fig.savefig(file_name, facecolor=fig.get_facecolor(), dpi=dpi)
            print(file_name)
        print('to', os.getcwd())

    return fig


if __name__ == '__main__':
    # Argument parsing.
    parser = argparse.ArgumentParser()
    parser.add_argument('--paths', nargs='+', default=[])
    parser.add_argument('--y_axis', default='episode_score')
    parser.add_argument('--x_label')
    parser.add_argument('--y_label')
    parser.add_argument('--interval', default='bounds')
    parser.add_argument('--window', type=int, default=1)
    parser.add_argument('--num_adv', type=int, default=1)
    parser.add_argument('--show_seeds', type=bool, default=False)
    parser.add_argument('--columns', type=int)
    parser.add_argument('--x_min', type=int)
    parser.add_argument('--x_max', type=int)
    parser.add_argument('--name')
    parser.add_argument('--save_formats', nargs='*', default=['png'])
    parser.add_argument('--seconds', type=int, default=0)
    parser.add_argument('--cmap')
    parser.add_argument('--legend_columns', type=int)
    parser.add_argument('--font_size', type=int, default=12)
    parser.add_argument('--font_family', default='serif')
    parser.add_argument('--legend_font_size', type=int)
    parser.add_argument('--legend_marker_size', type=int, default=10)
    parser.add_argument('--backend', default=None)
    parser.add_argument('--dpi', type=int, default=150)
    args = parser.parse_args()

    # Backend selection, e.g. agg for non-GUI.
    has_gui = True
    if args.backend:
        mpl.use(args.backend)
        has_gui = args.backend.lower() != 'agg'
    del args.backend

    # Fonts.
    plt.rc('font', family=args.font_family, size=args.font_size)
    if args.legend_font_size:
        plt.rc('legend', fontsize=args.legend_font_size)
    del args.font_family, args.font_size, args.legend_font_size

    seconds = args.seconds
    del args.seconds

    # Plot.
    start_time = time.time()
    fig = plot(**vars(args), fig=None)

    try:
        # Wait until the Window is closed if GUI.
        if seconds == 0:
            if has_gui:
                while plt.get_fignums() != []:
                    plt.pause(0.1)

        # Repeatedly plot, waiting a few seconds until interruption.
        else:
            while True:
                if has_gui:
                    while time.time() - start_time < seconds:
                        plt.pause(0.1)
                        assert plt.get_fignums() != []
                else:
                    time.sleep(seconds)
                start_time = time.time()
                plot(**vars(args), fig=fig)
    except:
        pass