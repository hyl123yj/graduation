import pandas as pd
import os

# 定义字段名称
header_fields = [
    "固定标识符", "国际编号", "数据记录数量", "序列号", "我国编号", "终结记录", "路径间隔小时数", "台风名称", "发布日期"
]
data_fields = [
    "时间", "等级", "纬度", "经度", "中心最低气压", "2分钟平均风速"
]

# 解析头记录
def parse_header(line):
    parts = line.split()
    if len(parts) < 9:  # 检查字段数量
        print(f"头记录字段不足，跳过该行: {line.strip()}")
        return None
    return {
        "固定标识符": parts[0],
        "国际编号": parts[1],
        "数据记录数量": int(parts[2]),
        "序列号": parts[3],
        "我国编号": parts[4],
        "终结记录": int(parts[5]),
        "路径间隔小时数": int(parts[6]),
        "台风名称": parts[7],
        "发布日期": parts[8]
    }

# 解析数据记录
def parse_data(line):
    parts = line.split()
    if len(parts) < 6:  # 检查字段数量
        print(f"数据记录字段不足，跳过该行: {line.strip()}")
        return None
    return {
        "时间": parts[0],
        "等级": int(parts[1]),
        "纬度": float(parts[2]) / 10,  # 转换为实际纬度
        "经度": float(parts[3]) / 10,  # 转换为实际经度
        "中心最低气压": int(parts[4]),
        "2分钟平均风速": int(parts[5])
    }

# 解析单个文件
def parse_file(file_path):
    typhoons = []
    with open(file_path, "r") as file:
        lines = file.readlines()
        i = 0
        while i < len(lines):
            # 解析头记录
            if lines[i].startswith("66666"):
                header = parse_header(lines[i])
                if header is None:  # 如果头记录解析失败，跳过该台风
                    i += 1
                    continue
                data_records = []
                i += 1
                # 解析数据记录
                for _ in range(header["数据记录数量"]):
                    if i >= len(lines):  # 检查是否超出文件范围
                        print(f"文件结束，跳过剩余数据记录")
                        break
                    record = parse_data(lines[i])
                    if record is not None:  # 如果数据记录解析成功，添加到列表中
                        data_records.append(record)
                    i += 1
                # 将头记录和数据记录合并
                typhoon = {**header, "数据记录": data_records}
                typhoons.append(typhoon)
            else:
                i += 1
    return typhoons

# 解析所有年份的数据
def parse_all_years(start_year, end_year, data_dir):
    all_data = []
    for year in range(start_year, end_year + 1):
        file_name = f"CH{year}BST.txt"
        file_path = os.path.join(data_dir, file_name)
        if os.path.exists(file_path):
            print(f"正在解析文件: {file_name}")
            typhoons = parse_file(file_path)
            all_data.extend(typhoons)
        else:
            print(f"文件不存在: {file_name}")
    return all_data

# 主程序
if __name__ == "__main__":
    # 设置数据目录和年份范围
    data_dir = "../data/bestroad"  # 替换为你的数据目录
    start_year = 1949
    end_year = 2023

    # 解析所有年份的数据
    all_typhoons = parse_all_years(start_year, end_year, data_dir)

    # 将数据转换为 DataFrame
    data = []
    for typhoon in all_typhoons:
        for record in typhoon["数据记录"]:
            data.append({**typhoon, **record})
    df = pd.DataFrame(data)

    # 保存为 CSV 文件
    output_file = "all_typhoon_data.csv"
    df.to_csv(output_file, index=False)
    print(f"数据解析完成，已保存为 {output_file}")