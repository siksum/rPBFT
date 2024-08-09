from collections import defaultdict

def groupby_sorted(data):
    grouped_data = defaultdict(list)
    
    for item in data:
        seq_num = item['message']['seq_num']
        grouped_data[seq_num].append(item)
    
    return dict(grouped_data)