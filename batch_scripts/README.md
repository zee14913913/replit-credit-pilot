# 批量上传脚本

此目录包含所有批量上传信用卡账单的脚本。

## 可用脚本

- `batch_upload_mbb.py` - Maybank批量上传
- `batch_upload_hlb.py` - Hong Leong Bank批量上传
- `batch_upload_uob.py` - UOB批量上传
- `batch_upload_hsbc.py` - HSBC批量上传
- `batch_upload_hsbc_ocr.py` - HSBC OCR批量上传

## 使用方法

```bash
python batch_scripts/batch_upload_mbb.py
```

## 注意事项

- 所有脚本使用新的DR/CR分类逻辑
- 确保PDF文件放置在正确的目录
- 脚本会自动检测银行类型并调用相应的parser
