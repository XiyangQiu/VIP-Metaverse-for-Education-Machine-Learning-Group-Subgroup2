# JSON 驱动长方体条

基础版仍位于上一层，本文件夹中的版本独立运行。

只需修改本文件夹的 `dimensions.json`，然后重新运行同一份
`rectangular_bar.py`。脚本总是读取自身同目录中的 JSON，运行时所在目录不限。

```json
{
  "units": "mm",
  "length": 100,
  "width": 20,
  "height": 10
}
```

`length`、`width`、`height` 分别沿 X、Y、Z 轴，最小角点为原点。
三个尺寸必须是大于零的有限数字；`units` 必须为 `"mm"`。
不接受缺失字段、零、负数、字符串、布尔值或非有限数字。

在当前电脑上运行（PowerShell）：

```powershell
& "C:\Users\lenovo\Documents\Codex\2026-10-20\text-to-cad-100-mm-20\work\.venv\Scripts\python.exe" "C:\Users\lenovo\Documents\Codex\2026-10-20\text-to-cad-100-mm-20\outputs\json_version\rectangular_bar.py"
```

若使用另一个已安装 `cadgen==0.7.10` 的 Python 环境，也可以在本文件夹中执行：

```powershell
python rectangular_bar.py
```

新 Python 环境可先执行一次 `python -m pip install -r requirements.txt`。

每次成功运行都会生成或更新本文件夹中的：

- `rectangular_bar.step`
- `rectangular_bar.stl`
- `rectangular_bar_validation.json`

验证报告重新读取导出的 STEP/STL，以 JSON 中的当前尺寸为基准检查包围盒、
体积、单实体/单连通分量、几何有效性与闭合性，并记录输入配置与文件校验值。
STL 不保存单位，导入其他软件时请选择毫米。

配置有误时，脚本输出具体字段的错误，返回退出码 2，不导出模型；
验证报告会更新为 `passed: false`，以免把前一次成功报告误认为本次结果。
生成或几何检查失败时返回退出码 1。失败后已有 STEP/STL 可能是上次结果；
只有本次报告 `passed: true` 才表示该配置通过验证。

`validate_geometry.py` 是验证辅助模块，请与主脚本和 JSON 保持在同一文件夹。
日后无需修改这两个 Python 文件。
