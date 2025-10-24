import re
import pandas as pd


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def extract_excel_data(file_path: str) -> list:
    """
    从Excel文件中提取指定列的数据，生成包含(label, question, FHIR_FSH)元组的列表
    """

    # 读取Excel文件，不跳过表头（第一行），数据从第二行开始为有效数据
    # 注意：pandas列索引从0开始，Excel列5→索引4，列6→索引5，列9→索引8
    df = pd.read_excel(file_path, engine='openpyxl')

    result = []
    # 从第二行开始遍历（DataFrame索引从0开始，对应Excel的第二行）
    for index, row in df.iterrows():
        # 提取对应列的值，转为字符串（处理可能的空值为空白字符串）
        _id = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""
        label = str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""
        question = str(row.iloc[5]) if pd.notna(row.iloc[5]) else ""
        deepquery_id = str(row.iloc[6]) if pd.notna(row.iloc[6]) else ""
        profile_id = str(row.iloc[7]) if pd.notna(row.iloc[7]) else ""
        fhir_fsh = str(row.iloc[8]) if pd.notna(row.iloc[8]) else ""

        result.append((_id, label, question, deepquery_id, profile_id, fhir_fsh))

    return result

