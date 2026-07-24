# 地块目录双人复核流程

1. 第二录入者不得复制首份 JSON；应从相同官方来源独立录入到 `content/tiles/review/`。
2. 先分别运行常规校验，再执行语义比对：

   ```bash
   python3 tools/content-validator/validate_tiles.py content/tiles/base-current.json \
     --diff content/tiles/review/base-current.second-pass.json
   ```

3. 工具忽略 JSON 键序、数组顺序和 `localSegmentId` 命名差异，但严格比较段端口、区带、符号、中心特征、随从区域、数量与旋转语义。
4. 所有差异必须回到来源逐项裁决，禁止只为了“跑绿”而复制任一方数据。
5. 零差异且双方确认来源后，才可将对应图案的 `verificationStatus` 从“已录入”提升为“已复核”。“已测试”仍须规则引擎场景测试通过。
