lst = [0, 1, 0, 0, 0, 1, 0, 1]

for i in range(2):
    try:
        index = lst.index(1)  # 첫 번째 1의 인덱스를 찾음
        lst[index] = 0        # 해당 인덱스의 값을 0으로 변경
    except ValueError:
        pass  # 리스트에 1이 없는 경우를 처리


print(lst)
