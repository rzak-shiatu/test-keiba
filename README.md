# 競馬出走表ジェネレーター

このリポジトリは、TOML で記述したレース情報から競馬の出走表（評価表）を HTML として出力するための簡単なツールです。スクリーンショットで示されたような評価表を、共通のテンプレートに従って素早く作成できます。

## 必要要件

- Python 3.11 以上（標準ライブラリのみを使用しています）

## 使い方

1. レース情報を TOML 形式で用意します。テンプレートとして `data/sample_race.toml` を参照してください。
2. 次のコマンドで HTML ファイルを生成します。

   ```bash
   python generate_race_table.py data/sample_race.toml output/sample_race.html
   ```

   `output` 引数を省略した場合は、入力ファイルと同じ場所に `.html` を付けたファイルが出力されます。

3. 生成された HTML ファイルをブラウザで開くと、評価付きの出走表を確認できます。

## TOML ファイルの構成

```toml
[race]
title = "今回の査定評価に関わる項目"   # 表のタイトル
subtitle = "天皇賞（春） 芝3200m (右外 C)" # 任意: サブタイトル
additional_columns = ["前走", "ローテ"]     # 任意: 評価以外に表示するカスタム列
footnote = "注記をここに記述"                # 任意: 表下部に表示するフッター

distance_note = "※芝2000m以上/1600〜1800m"  # 任意: タイトル下の補足

[[criteria]]
key = "枠順"
label = "枠順"
description = "内枠がプラス評価。"

[[criteria]]
key = "距離適性"
label = "距離適性"

# ... 任意の数だけ criteria を追加できます

[legend]
枠順 = "評価基準を説明するテキスト"
距離適性 = "評価基準を説明するテキスト"

[[horses]]
post_position = 1
number = 1
name = "アスクワイルドモア"
sex_age = "牡4"
weight = "58"
jockey = "岩田望来"
running_style = "差し"
ratings = { 枠順 = "A", 距離適性 = "B" }
notes = { 前走 = "日経賞 6着", ローテ = "中3週" }
comments = "内枠を活かせれば上位争いも。"

# ... 出走馬の数だけ追加
```

### 各セクションの説明

- `[race]`
  - `title`, `subtitle`, `distance_note` はヘッダーに表示されます。
  - `additional_columns` は各馬固有のメモ情報（`notes` のキー）を列として表示します。文字列を指定するとキーと表示ラベルが同じになり、`{ key = "identifier", label = "表示名" }` のようにテーブルで書くと表示名だけを変えられます。
  - `footnote` は表の下部に小さく表示する備考欄です。
- `[[criteria]]`
  - 評価軸を定義します。`key` はデータ上の識別子、`label` は表に表示するラベルです。
  - `description` を設定すると、表下部の「評価基準」欄に説明として表示されます（`legend` に同じキーの説明がある場合は `legend` が優先されます）。
- `[legend]`
  - 各評価軸に対する補足説明を自由に記述できます。省略した場合は `criteria` の `description` がそのまま表示されます。
- `[[horses]]`
  - 1 頭につき 1 テーブル。`ratings` には `key` に対応する評価値（S/A/B/C…など）を指定します。
  - `notes` は `additional_columns` で定義した列に対応する文字列を指定します。
  - `running_style` や `comments` は任意です。値が設定されている場合のみ列が表示されます。

## ブラケット色について

枠番（1〜8）に応じて JRA の公式色に近い配色でセル背景色を自動設定しています。

| 枠番 | 色 | 文字色 |
| ---- | --- | ------ |
| 1 | 白 (#ffffff) | 黒 |
| 2 | 黒 (#000000) | 白 |
| 3 | 赤 (#ff4b4b) | 白 |
| 4 | 青 (#1a7cff) | 白 |
| 5 | 黄 (#ffd447) | 黒 |
| 6 | 緑 (#3ab66b) | 白 |
| 7 | 橙 (#ff7f27) | 黒 |
| 8 | 桃 (#ff7fd1) | 黒 |

## サンプルデータ

- `data/sample_race.toml`: サンプルの入力ファイル
- `output/sample_race.html`: 上記の TOML から生成したサンプル（`python generate_race_table.py data/sample_race.toml output/sample_race.html` で生成できます）

## テスト

変更を加えた際は次のコマンドでユニットテストを実行して動作を確認できます。

```bash
python -m unittest
```

## ライセンス

このリポジトリ内のコードは MIT ライセンスで提供されています。
