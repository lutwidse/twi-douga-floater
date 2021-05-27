# twi-douga-floater

twi-douga のランキングを操作できるスクリプト

## 諸注意

このレポジトリは学習目的の為に作られました。当該するサービスを侵害、及び妨害する意図は一切ありません。  
また、本レポジトリに存在するコードを使用して何かしらの問題が生じたとしても、当方では一切の責任を負いかねます。

## 使い方

`$ pip install -r requirements.txt`  
`$ python twi-douga-floater.py -tv 50 -p proxies.txt -v videos.txt`
- コマンドライン引数
  - --target_views 目標の閲覧数
  - --proxies プロキシ (対応プロトコル http/https socks5)
  - --videos 動画
- オプション
    - --threads スレッド数
  
詳しくは[サンプル](example/)を参照  
~~コードを読んだほうが早い、他の設定値はハードコーディング~~

## めいぷーるプルリクエスト

来る者拒まず
