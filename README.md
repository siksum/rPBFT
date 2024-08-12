# PBFT Simulator

### usage
```shell
python3 main.py [algorithm] [options]
```

- algorithm : PBFT / rPBFT
- PBFT execution example
    ```shell
    python3 main.py PBFT --nodes 10 --faulty_nodes 1
    ```
- rPBFT execution example
    ```shell
    python3 main.py rPBFT --nodes 10 --model [infant/wearout/random/bathtub]
    ```
- Visualization(in Utils directory)
    ```shell
    python3 visualizer.py 
    ```
    - It can be used if output.txt is in Utils folder.
---

## TODO
[Today] : 2024.08.12
- 소켓 관련해서 터지는 문제
- 테스트 목적에 따라 View-Change는 구현하지 않음 -> 따로 PBFT 만들어보기에서 해볼 예정
- SG-PBFT 구현체 복원
- 노드수에 따른 합의 성공률 테스트