import re
import matplotlib.pyplot as plt

def parse_log(log_lines):
    nodes = set()
    messages = []
    
    for line in log_lines:
        if 'Client' in line:
            nodes.add('C')
        else:
            match = re.search(r'Node: (\d+)', line)
            if match:
                nodes.add(match.group(1))
        
        if ("[Recieve] Primary Node:" and "content: {'stage': 'REQUEST',") in line:
            messages.append(('C', re.search(r'Primary Node: (\d+)', line).group(1), 'request'))
        # elif 'stage: REQUEST' in line:
        #     messages.append(('C', re.search(r'Node: (\d+)', line).group(1), 'request'))
        elif 'PRE-PREPARE' in line:
            messages.append((re.search(r"'node_id': (\d+)", line).group(1), re.search(r'Node: (\d+)', line).group(1), 'pre-prepare'))
        elif 'PREPARE' in line:
            messages.append((re.search(r"'node_id': (\d+)", line).group(1), re.search(r'Node: (\d+)', line).group(1), 'prepare'))
        elif 'COMMIT' in line:
            messages.append((re.search(r"'node_id': (\d+)", line).group(1), re.search(r'Node: (\d+)', line).group(1), 'commit'))
        elif 'REPLY' in line:
            messages.append((re.search(r"'node_id': (\d+)", line).group(1), 'C', 'reply'))
    
    return sorted(list(nodes)), messages

def visualize_pbft(nodes, messages):
    stages = ['request', 'pre-prepare', 'prepare', 'commit', 'reply']
    fig, ax = plt.subplots(figsize=(len(stages)*2, len(nodes)))
    
    # 노드 순서를 오름차순으로 정렬
    sorted_nodes = sorted(nodes, key=lambda x: int(x) if x != 'C' else -1, reverse=True)
    
    for i, node in enumerate(sorted_nodes):
        ax.plot([0, len(stages)], [i, i], 'k-', linewidth=1)
        ax.text(-0.1, i, node, ha='right', va='center')
    
    arrow_style = {
        'request': {'color': 'blue', 'style': '->'},
        'pre-prepare': {'color': 'green', 'style': '->'},
        'prepare': {'color': 'orange', 'style': '->'},
        'commit': {'color': 'red', 'style': '->'},
        'reply': {'color': 'purple', 'style': '->'}
    }
    
    for message in messages:
        sender, receiver, step = message
        sender_idx = sorted_nodes.index(sender)
        receiver_idx = sorted_nodes.index(receiver)
        stage_idx = stages.index(step)
        
        arrow = arrow_style[step]
        
        if step == 'request':
            ax.annotate('', xy=(1, receiver_idx), xytext=(0, sender_idx),
                        arrowprops=dict(arrowstyle=arrow['style'], color=arrow['color'], shrinkA=5, shrinkB=5))
        elif step == 'reply':
            ax.annotate('', xy=(len(stages), receiver_idx), xytext=(stage_idx, sender_idx),
                        arrowprops=dict(arrowstyle=arrow['style'], color=arrow['color'], shrinkA=5, shrinkB=5))
        else:
            ax.annotate('', xy=(stage_idx+1, receiver_idx), xytext=(stage_idx, sender_idx),
                        arrowprops=dict(arrowstyle=arrow['style'], color=arrow['color'], shrinkA=5, shrinkB=5))
    
    ax.set_xticks(range(len(stages)))
    ax.set_xticklabels(stages)
    ax.set_xlim(-0.2, len(stages))
    ax.set_ylim(-0.5, len(nodes)-0.5)
    ax.get_yaxis().set_visible(False)
    
    plt.tight_layout()
    plt.show()

log_text = open('b.txt', 'r').readlines()

nodes, messages = parse_log(log_text)
visualize_pbft(nodes, messages)