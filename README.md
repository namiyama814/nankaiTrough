# NSCI（南海トラフ社会貢献指数）

NSCIは、南海トラフ巨大地震の際に企業が提供できる**具体的な機能**を、公開・記録可能なデータから調べるための指標です。会社の売上や株価、業種ラベルは使いません。

社会には食物連鎖のピラミッドのような支え合いがあります。たとえば電力が止まれば通信が難しくなり、通信が止まれば被害情報共有や救助にも影響します。NSCIはまずこの「機能のつながり」を評価し、その後で各企業が実際に提供できる力と被災地域への対応力を組み合わせます。

## 計算式

`NSCI = FCI × ECI × GCI`、表示用の点数は `NSCI_100 = NSCI × 100` です。すべて0〜1（表示は0〜100）の範囲です。

- **FCI（機能重要度）**: 下流への影響範囲、ネットワークのボトルネック度、必要になる早さ、救命などの重要な終点へ届く度合いの平均です。
- **ECI（実行能力）**: `CapabilityScore` と `DeploymentRate` の平均です。能力は同じ機能・同じmetricを提供する企業間だけで比較します。過去災害実績が`unknown`なら「実績なし」にはせず、情報不足として扱います。
- **GCI（地域適合度）**: 南海トラフ想定地域の需要に対して、根拠付きの企業能力でどこまでカバーできるかを需要加重で計算します。

## データの作り方

`data/` のCSV見本を複製して使います。企業名や機能名はコード内に固定されていません。

- `functions.csv` と `dependencies.csv` で社会機能と依存関係を定義します。依存関係は、許可済みの根拠種別を持つ `source_id` が必要です。
- `metric_definitions.csv` は機能ごとの能力metric、単位、良い方向、必須性を固定します。企業の値を入れる `company_metrics.csv` 側でこれらを上書きできません。
- `evidence_sources.csv` は根拠の台帳です。`source_reference` は必須、URLは任意です。専門家ヒアリングなどURLのない一次情報も管理できます。
- `disaster_deployments.csv` の `deployment_status` は `deployed`、`not_deployed`、`unknown` のいずれかです。
- `regional_need.csv` と `company_regional_capacity.csv` は単位を完全に一致させます。自動換算はしません。

既定では必須metric、確認済み災害実績ともに100%のcoverageが必要です。また比較対象企業が3社未満のmetricは比較不能（NA）です。設定は `config.yaml` で変更できますが、欠損値を推測して埋めることはありません。

## 実行方法

Python 3.12以上で依存関係を入れます。

```bash
python -m pip install -r requirements.txt
python -m nsci validate --data ./data
python -m nsci calculate --data ./data --output ./output --config ./config.yaml
python -m nsci graph --data ./data --output ./output
pytest
```

`output/company_function_scores.csv` は機能別のFCI、CapabilityScore、DeploymentRate、ECI、GCI、NSCIとcoverage・状態を示します。`company_scores.csv` は有効な機能だけをtop-k平均した企業値です。情報が足りない行は0点ではなくNA／`insufficient_data`として表示され、順位に混ぜません。

`evidence_report.csv` は全入力行と根拠台帳を結合した一覧です。`dependency_graph.graphml` はGephiなどで開け、PNGは簡易図です。

## このモデルの限界

完全に主観を排除できるわけではありません。どの機能をモデルへ含めるか、どの依存関係を認めるかには研究設計上の判断が残ります。そのため、依存関係と数値には必ず根拠資料を紐付け、計算を始める前にルールを固定します。NSCIは根拠のない「重要度5点」のような評価を置き換えるものですが、データの質を超えて結論を保証するものではありません。
