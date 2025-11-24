#!/usr/bin/env python3
"""
Google Document AI Custom Processor Schema 创建脚本
自动创建马来西亚信用卡账单提取器的Schema配置
"""
import os
import json
from pathlib import Path
from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account


class DocumentAISchemaCreator:
    """Document AI Schema创建器"""
    
    def __init__(self):
        """初始化"""
        self.project_id = os.getenv('GOOGLE_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT_ID')
        self.location = os.getenv('GOOGLE_LOCATION', 'us')
        
        if not self.project_id:
            raise ValueError("缺少环境变量: GOOGLE_PROJECT_ID 或 GOOGLE_CLOUD_PROJECT_ID")
        
        # 初始化客户端
        json_content = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if json_content:
            credentials_info = json.loads(json_content)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            self.client = documentai.DocumentProcessorServiceClient(credentials=credentials)
        else:
            self.client = documentai.DocumentProcessorServiceClient()
    
    def get_schema_definition(self) -> dict:
        """获取Schema定义"""
        return {
            "displayName": "Malaysian Credit Card Statement Extractor",
            "description": "提取马来西亚银行信用卡账单关键字段",
            "entityTypes": [
                # 基本信息字段
                {
                    "name": "statement_date",
                    "displayName": "账单日期",
                    "baseTypes": ["datetime"],
                    "occurrenceType": "REQUIRED_ONCE"
                },
                {
                    "name": "due_date",
                    "displayName": "到期日",
                    "baseTypes": ["datetime"],
                    "occurrenceType": "REQUIRED_ONCE"
                },
                {
                    "name": "card_number",
                    "displayName": "信用卡号码",
                    "baseTypes": ["string"],
                    "occurrenceType": "REQUIRED_ONCE"
                },
                {
                    "name": "cardholder_name",
                    "displayName": "持卡人姓名",
                    "baseTypes": ["string"],
                    "occurrenceType": "REQUIRED_ONCE"
                },
                {
                    "name": "bank_name",
                    "displayName": "银行名称",
                    "baseTypes": ["string"],
                    "occurrenceType": "REQUIRED_ONCE"
                },
                
                # 金额字段
                {
                    "name": "total_amount",
                    "displayName": "总金额",
                    "baseTypes": ["money"],
                    "occurrenceType": "REQUIRED_ONCE"
                },
                {
                    "name": "minimum_payment",
                    "displayName": "最低还款额",
                    "baseTypes": ["money"],
                    "occurrenceType": "REQUIRED_ONCE"
                },
                {
                    "name": "previous_balance",
                    "displayName": "上期余额",
                    "baseTypes": ["money"],
                    "occurrenceType": "OPTIONAL_ONCE"
                },
                {
                    "name": "new_charges",
                    "displayName": "本期新增消费",
                    "baseTypes": ["money"],
                    "occurrenceType": "OPTIONAL_ONCE"
                },
                {
                    "name": "payments_credits",
                    "displayName": "本期还款/贷记",
                    "baseTypes": ["money"],
                    "occurrenceType": "OPTIONAL_ONCE"
                },
                
                # 交易明细表格
                {
                    "name": "transactions",
                    "displayName": "交易记录",
                    "baseTypes": ["table"],
                    "occurrenceType": "OPTIONAL_MULTIPLE",
                    "properties": [
                        {
                            "name": "transaction_date",
                            "displayName": "交易日期",
                            "baseTypes": ["date"],
                            "occurrenceType": "REQUIRED_ONCE"
                        },
                        {
                            "name": "description",
                            "displayName": "交易描述",
                            "baseTypes": ["string"],
                            "occurrenceType": "REQUIRED_ONCE"
                        },
                        {
                            "name": "amount",
                            "displayName": "金额",
                            "baseTypes": ["money"],
                            "occurrenceType": "REQUIRED_ONCE"
                        },
                        {
                            "name": "category",
                            "displayName": "分类",
                            "baseTypes": ["string"],
                            "occurrenceType": "OPTIONAL_ONCE",
                            "enumValues": ["Owners", "GZ", "Suppliers"]
                        }
                    ]
                }
            ]
        }
    
    def save_schema_json(self, output_path: str = "config/document_ai_schema.json"):
        """保存Schema为JSON文件"""
        schema = self.get_schema_definition()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Schema已保存到: {output_file}")
        return str(output_file)
    
    def create_custom_processor(self, display_name: str = "CreditCard-Statement-Extractor"):
        """
        创建自定义Processor（需要手动在Console完成）
        此函数生成配置文件供参考
        """
        print("="*80)
        print("🚀 创建Google Document AI Custom Processor")
        print("="*80)
        
        # 保存Schema
        schema_file = self.save_schema_json()
        
        print("\n📋 Schema包含以下字段:")
        schema = self.get_schema_definition()
        
        print("\n基本信息字段 (5个):")
        for entity in schema['entityTypes'][:5]:
            print(f"   - {entity['name']:20s} ({entity['baseTypes'][0]})")
        
        print("\n金额字段 (5个):")
        for entity in schema['entityTypes'][5:10]:
            print(f"   - {entity['name']:20s} ({entity['baseTypes'][0]})")
        
        print("\n交易表格 (1个):")
        table_entity = schema['entityTypes'][10]
        print(f"   - {table_entity['name']:20s} ({table_entity['baseTypes'][0]})")
        print(f"     列定义:")
        for prop in table_entity['properties']:
            print(f"       * {prop['name']:20s} ({prop['baseTypes'][0]})")
        
        print("\n" + "="*80)
        print("⚠️  注意：Custom Processor需要在Google Cloud Console手动创建")
        print("="*80)
        
        print(f"\n📝 步骤:")
        print(f"1. 访问: https://console.cloud.google.com/ai/document-ai/processors")
        print(f"2. 选择项目: {self.project_id}")
        print(f"3. 点击 'CREATE PROCESSOR'")
        print(f"4. 选择 'Document OCR' 或 'Custom Document Extractor'")
        print(f"5. Processor名称: {display_name}")
        print(f"6. 位置: {self.location}")
        print(f"7. 上传训练样本并标注字段")
        print(f"8. 使用Schema文件: {schema_file}")
        
        print("\n💾 Schema配置已保存，可直接用于创建Processor")
        
        return schema_file
    
    def generate_training_guide(self):
        """生成训练指南"""
        guide = """
================================================================================
Document AI 训练样本标注指南
================================================================================

📁 准备样本PDF:
   - 最少: 20个不同银行的账单PDF
   - 推荐: 50-100个样本
   - 需要覆盖: AmBank, HSBC, Standard Chartered, UOB, Hong Leong, OCBC

📝 标注步骤:

1. 上传PDF到Document AI Console
2. 使用标注工具框选以下字段:

   基本信息:
   ☐ statement_date - 框选 "28 MAY 25"
   ☐ due_date - 框选 "17 JUN 25"
   ☐ card_number - 框选 "4031 4899 9530 6354" (完整16位)
   ☐ cardholder_name - 框选 "CHEOK JUN YOON"
   ☐ bank_name - 框选 "AmBank"

   金额字段:
   ☐ total_amount - 框选 "RM 5,234.56"
   ☐ minimum_payment - 框选 "RM 261.73"
   ☐ previous_balance - 框选 "RM 4,123.45"
   ☐ new_charges - 框选 "RM 1,234.56"
   ☐ payments_credits - 框选 "RM 123.45 CR"

   交易表格:
   ☐ transactions - 框选整个表格区域
     然后逐列标注:
     - transaction_date: "15 MAY"
     - description: "MCDONALD'S-KOTA WARISAN"
     - amount: "36.60"
     - category: "Owners" (可选)

3. 验证标注:
   - 检查每个字段是否完整
   - 确认金额包含货币符号
   - 验证日期格式正确

4. 保存并训练:
   - 标注完20+样本后点击 "TRAIN"
   - 训练时间: 约2-4小时
   - 训练完成后测试准确度

5. 测试验证:
   - 使用未标注的PDF测试
   - 目标准确度: ≥95%

================================================================================
        """
        
        guide_file = Path("docs/document_ai_training_guide.txt")
        guide_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)
        
        print(guide)
        print(f"\n✅ 训练指南已保存到: {guide_file}")
        
        return str(guide_file)


def main():
    """主函数"""
    print("="*80)
    print("Google Document AI Schema 创建工具")
    print("="*80)
    
    try:
        creator = DocumentAISchemaCreator()
        
        # 创建Schema配置
        schema_file = creator.create_custom_processor()
        
        # 生成训练指南
        guide_file = creator.generate_training_guide()
        
        print("\n" + "="*80)
        print("✅ 完成！")
        print("="*80)
        print(f"\n📄 生成的文件:")
        print(f"   1. Schema配置: {schema_file}")
        print(f"   2. 训练指南: {guide_file}")
        print(f"   3. 详细文档: docs/document_ai_schema.md")
        
        print("\n🎯 下一步:")
        print("   1. 在Google Cloud Console创建Custom Processor")
        print("   2. 上传并标注训练样本")
        print("   3. 训练模型")
        print("   4. 测试验证")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
