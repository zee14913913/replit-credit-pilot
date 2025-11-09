#!/usr/bin/env python3
print("脚本开始...")

import sys
print("导入sys成功")

import csv
print("导入csv成功")

import psycopg2
print("导入psycopg2成功")

import os
print("导入os成功")

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"DATABASE_URL: {DATABASE_URL[:20]}...")

print("连接数据库...")
con = psycopg2.connect(DATABASE_URL)
print("连接成功")

cur = con.cursor()
print("创建游标成功")

cur.execute("SELECT DISTINCT company FROM loan_products_ultimate")
print("执行查询成功")

completed = [row[0] for row in cur.fetchall()]
print(f"获取到{len(completed)}家已完成公司")

cur.close()
con.close()
print("数据库关闭")

print("读取CSV...")
CSV_INPUT = "/home/runner/workspace/attached_assets/New 马来西亚贷款机构与平台全官网_完整版.csv_1762667764316.csv"

with open(CSV_INPUT, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    institutions = [{'name': row[0].strip(), 'website': row[1].strip()} for row in reader if len(row) >= 2]

print(f"读取到{len(institutions)}家机构")

print("✅ 所有测试通过！")
