import os
import numpy as np

def logFileDivSaveThread(ptn_file_names, ptn_data_list, selected_ptn_index):
    """
    PTN 로그 파일을 세그먼트로 나누어 저장합니다.
    
    :param ptn_file_names: PTN 파일 이름 리스트
    :param ptn_data_list: PTN 데이터 리스트
    :param selected_ptn_index: 선택된 PTN 파일의 인덱스
    :return: 저장된 세그먼트 파일 경로 리스트
    """
    # 선택된 PTN 파일의 데이터
    ptn_data = ptn_data_list[selected_ptn_index]
    ptn_file_name = ptn_file_names[selected_ptn_index]

    # 세그먼트 폴더 생성
    segment_folder = f"./{ptn_file_name}_linesegment"
    os.makedirs(segment_folder, exist_ok=True)

    # 세그먼트 파일 경로 리스트
    segment_files = []

    # MGN 데이터에서 세그먼트 시간 정보 추출 (예시: MGN 데이터가 없는 경우, 임의의 시간 간격 사용)
    segment_times = np.linspace(0, ptn_data[-1, 0], num=len(ptn_data) // 10)  # 임의의 시간 간격 생성

    # 각 세그먼트에 대해 처리
    for i in range(len(segment_times) - 1):
        segment_start = segment_times[i]
        segment_end = segment_times[i + 1]

        # 세그먼트에 해당하는 데이터 선택
        segment_indices = np.where((ptn_data[:, 0] >= segment_start) & (ptn_data[:, 0] < segment_end))[0]
        segment_data = ptn_data[segment_indices]

        # X, Y 위치 및 크기 변환 (예시: 임의의 공식 적용)
        segment_data[:, 1] = (segment_data[:, 1] / XPOSGAIN) + XPOSOFFSET  # X 위치
        segment_data[:, 2] = (segment_data[:, 2] / YPOSGAIN) + YPOSOFFSET  # Y 위치
        segment_data[:, 3] = segment_data[:, 3] / XPOSGAIN  # X 크기
        segment_data[:, 4] = segment_data[:, 4] / YPOSGAIN  # Y 크기

        # 세그먼트 데이터를 바이너리 파일로 저장
        segment_file_name = f"{segment_folder}/{ptn_file_name}_linesegment{i + 1}.ptn"
        segment_data.astype(np.uint16).tofile(segment_file_name)
        segment_files.append(segment_file_name)

    print(f"PTN 파일 세그먼트 저장 완료: {segment_folder}")
    return segment_files