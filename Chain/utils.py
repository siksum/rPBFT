from collections import defaultdict

def groupby_sorted(data):
    grouped_data = defaultdict(list)
    
    for item in data:
        seq_num = item['message']['seq_num']
        grouped_data[seq_num].append(item)
    
    return dict(grouped_data)

def remove_duplicates(messages):
    seen = set()
    unique_messages = []
    
    for message in messages:
        key = (message['node_id_to'], message['node_id_from'], message['message']['digest'])
        
        if key not in seen:
            unique_messages.append(message)
            seen.add(key)
    
    return unique_messages

def check_duplicate(new_message, received_messages):
    check_this = (new_message['node_id_to'], new_message['node_id_from'], new_message['message']['digest'])
    for message in received_messages:
        key = (message['node_id_to'], message['node_id_from'], message['message']['digest'])
        if key == check_this:
            return True
    return False