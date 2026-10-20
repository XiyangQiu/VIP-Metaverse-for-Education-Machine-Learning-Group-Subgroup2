全部 6 项符合预期。成功组均重新读取归档 STEP、STL，确认尺寸和体积。

| 测试 | 实测尺寸（mm）或明确错误 | 体积（mm³） | 退出码 | 报告 passed | 测试结果 |
|---|---|---:|---:|---|---|
| ① | 80 × 30 × 5 | 12,000 | 0 | true | 通过 |
| ② | 50.5 × 10 × 2 | 1,010 | 0 | true | 通过 |
| ③ length=0 | length 必须大于 0 | — | 2 | false | 按预期拒绝 |
| ④ width=-20 | width 必须大于 0 | — | 2 | false | 按预期拒绝 |
| ⑤ 缺少 height | 缺少必填字段 height | — | 2 | false | 按预期拒绝 |
| 恢复 | 150 × 20 × 10 | 30,000 | 0 | true | 通过 |

当前输入、STEP/STL 和验证报告已恢复为 150 × 20 × 10 mm（30,000 mm³），passed=true。
原 Python 脚本、验证模块、基础版本和先前 150 mm 测试归档保持不变。

每组子文件夹保存 dimensions.json、stdout.log、stderr.log、run.log、rectangular_bar_validation.json、run_result.json。
成功组还保存 STEP/STL、independent_verification.json 和已检查的 preview.png。
失败组未另存模型，且确认上次有效导出文件未被修改。
各组 manifest.json 保存文件校验值；source 文件夹保存本次使用的源代码和依赖版本。
