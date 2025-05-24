import openpyxl

def logFileExcelSaveThread(ptn_file_names, ptn_data_list, mgn_file_names, mgn_data_list, save_ptn_as_excel=False, save_mgn_as_excel=False):
    """
    로그 파일 데이터를 Excel 파일로 저장합니다.
    
    :param ptn_file_names: PTN 파일 이름 리스트
    :param ptn_data_list: PTN 데이터 리스트
    :param mgn_file_names: MGN 파일 이름 리스트
    :param mgn_data_list: MGN 데이터 리스트
    :param save_ptn_as_excel: PTN 데이터를 Excel로 저장할지 여부 (기본값: False)
    :param save_mgn_as_excel: MGN 데이터를 Excel로 저장할지 여부 (기본값: False)
    :return: 저장된 파일 경로 리스트
    """
    saved_files = []

    # PTN 데이터를 Excel로 저장
    if save_ptn_as_excel:
        for i, ptn_file_name in enumerate(ptn_file_names):
            # Excel 파일 이름 생성
            excel_file_name = ptn_file_name.replace(".ptn", "_ptn.xlsx")
            
            # Excel 파일 생성
            wb = openpyxl.Workbook()
            ws = wb.active

            # 헤더 작성
            ws.append(["Time (ms)", "X Position", "Y Position", "MU count"])

            # 데이터 작성
            for row in ptn_data_list[i]:
                ws.append([row[0], row[1], row[2], row[5]])

            # 파일 저장
            wb.save(excel_file_name)
            saved_files.append(excel_file_name)
            print(f"PTN 데이터 저장 완료: {excel_file_name}")

    # MGN 데이터를 Excel로 저장
    if save_mgn_as_excel:
        for i, mgn_file_name in enumerate(mgn_file_names):
            # Excel 파일 이름 생성
            excel_file_name = mgn_file_name.replace(".mgn", "_mgn.xlsx")
            
            # Excel 파일 생성
            wb = openpyxl.Workbook()
            ws = wb.active

            # 헤더 작성
            ws.append(["Segment number", "Time (ms)", "X Position", "Y Position"])

            # 데이터 작성
            for j, row in enumerate(mgn_data_list[i]):
                ws.append([j + 1, row[0], row[3], row[4]])

            # 파일 저장
            wb.save(excel_file_name)
            saved_files.append(excel_file_name)
            print(f"MGN 데이터 저장 완료: {excel_file_name}")

    return saved_files