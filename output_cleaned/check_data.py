import pandas as pd
import ast

# 加载数据
df = pd.read_csv('./vispub_final.csv')

# 挑选一个较新的年份（比如 2024）
year_new = 2025
year_old = 2024

# 找到新年份中包含引用的文章
df_new = df[df['year'] == year_new].dropna(subset=['oa_referenced_works'])

print(f"--- {year_new} 年数据统计 ---")
print(f"总文章数: {len(df[df['year'] == year_new])}")
print(f"带有引用信息的文章数: {len(df_new)}")

# 检查是否有引用指向旧年份
all_old_ids = set(df[df['year'] == year_old]['oa_openalex_id'].unique())

found_link = False
for idx, row in df_new.head(50).iterrows():
    try:
        refs = ast.literal_eval(row['oa_referenced_works'])
        # 检查这篇论文的引用列表中，有没有 ID 出现在旧年份的文章集合里
        intersect = set(refs).intersection(all_old_ids)
        if intersect:
            print(f"\n成功匹配！文章 '{row['title']}' 引用了 {year_old} 年的 {len(intersect)} 篇论文。")
            print(f"示例引用 ID: {list(intersect)[0]}")
            found_link = True
            break
    except:
        continue

if not found_link:
    print(f"\n结果: 在抽样的前 50 篇 {year_new} 年论文中，没有发现对 {year_old} 年论文的引用。")