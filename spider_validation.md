# 爬虫校验报告

- 生成时间: 2026-05-12T07:02:01+08:00
- 并发线程数: 16
- 总耗时(ms): 54.951秒
- 总数: 69
- 成功: 52
- 失败: 17

## 阶段失败统计

| 阶段 | 数量 |
| --- | ---: |
| 模块加载 | 0 |
| 初始化 | 0 |
| 首页分类 | 1 |
| 分类列表 | 5 |
| 视频详情 | 0 |
| 播放地址 | 1 |
| 地址校验 | 5 |
| 未预期异常 | 5 |

## 明细结果

| 爬虫 | 状态 | 失败阶段 | 总耗时 | 模块加载 | 初始化 | 首页分类 | 分类列表 | 视频详情 | 播放地址 | 地址校验 | 返回地址 | 错误信息 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 4K指南 | 成功 |  | 8.971秒 | 176.226ms | 0.001ms | 0.003ms | 4.059秒 | 4.426秒 | 0.004ms | 257.393ms | https://pan.xunlei.com/s/VOsM-4grxeaeMV65z_HmIk5tA1?pwd=g3hz |  |
| AAZ音乐 | 失败 | 未预期异常 | 10.239秒 | 175.634ms | 0.001ms | 10.059秒 | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='www.aaz.cx', port=443): Read timed out. (read timeout=10) |
| PPnix | 成功 |  | 6.736秒 | 256.966ms | 0.0ms | 0.001ms | 3.359秒 | 2.186秒 | 0.01ms | 933.859ms | https://www.ppnix.com/info/m3u8/8140/1080P.m3u8 |  |
| QQ音乐 | 成功 |  | 2.185秒 | 210.153ms | 0.007ms | 0.003ms | 619.423ms | 936.789ms | 339.754ms | 62.912ms | https://isure.stream.qqmusic.qq.com/F0000014qLXa1JrJ11.flac?guid=951269c2f0cbf4cbeba06cd122a3a676&vkey=2B4EB108336A5D74D2A0D4C4309F44329E8D51C82AA9FC16FA5683EFC10807C7D4F9B58AC38314B45BD0546B05033A2301EA110598BD6A33__v2b9abc6c&uin=1152921504846230218&fromtag=119114&redirect=1 |  |
| libvio | 失败 | 分类列表 | 5.031秒 | 177.187ms | 0.001ms | 0.002ms | 2.838秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| youknow | 成功 |  | 15.66秒 | 180.14ms | 0.001ms | 0.001ms | 4.469秒 | 3.15秒 | 4.181秒 | 3.639秒 | https://vip.dytt-cinema.com/20250215/2096_194cf6c2/index.m3u8 |  |
| 不太灵 | 失败 | 播放地址 | 11.738秒 | 174.921ms | 0.0ms | 2.221秒 | 3.063秒 | 2.1秒 | 0.006ms | 0.0ms |  | playerContent 未返回播放地址 |
| 世纪音乐 | 失败 | 地址校验 | 1.284秒 | 181.566ms | 0.001ms | 280.64ms | 0.005ms | 138.852ms | 0.006ms | 164.511ms | https://www.4c44.com/data/down.php?ac=music&id=hkwyytdecc | HTTP 403 |
| 两个BT | 成功 |  | 15.673秒 | 212.88ms | 0.001ms | 0.001ms | 3.17秒 | 1.977秒 | 7.971秒 | 2.34秒 | https://zijieapi.douyinbyte.com/m3u8/9c8b45a454bca9240caef92666d31099.m3u8 |  |
| 乌云影视 | 成功 |  | 20.73秒 | 174.983ms | 0.0ms | 4.054秒 | 3.212秒 | 9.66秒 | 0.019ms | 3.587秒 | https://d1jdnmkc1n5cn4.cloudfront.net/gen_overseas/https://s2.bfllvip.com/video/yanxiaxing/a6ef854c0c1f/index.m3u8 |  |
| 乐兔 | 失败 | 未预期异常 | 10.242秒 | 174.371ms | 0.004ms | 0.001ms | 10.023秒 | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='www.letu.me', port=443): Read timed out. (read timeout=10) |
| 二小 | 成功 |  | 7.882秒 | 209.867ms | 0.001ms | 0.001ms | 4.418秒 | 3.026秒 | 0.011ms | 223.564ms | https://pan.quark.cn/s/b3e194803b59 |  |
| 人人电影 | 失败 | 分类列表 | 8.559秒 | 206.017ms | 0.001ms | 0.002ms | 3.514秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 人人视频 | 失败 | 地址校验 | 2.877秒 | 169.896ms | 0.001ms | 303.983ms | 264.102ms | 275.832ms | 442.185ms | 178.171ms | https://a3fkpcuk2gkkpmr.302.fledgecloud.com:56782/zj-302-cdn.bwcgee.cn/307ba6dcef6871ef85774531959c0402/67389eb6001c4a1e9b1f2f7ca2a82dc1-1b1785a818fc693827ab9628d26d600b-ld.mp4?auth_key=1778554924-3236661dccf8a8bb846f40384bc08240-0-cce54c03d50f226cb0b5c56c22c8ea6d&clientType=web_pc&clientVersion=1.0.0&parseUsage=PLAY&uid=0&rk=ef18ca7e261a48d6a45924a5a9c8a7c6&hevc=false&seasonId=51705 | HTTP 403 |
| 优酷 | 成功 |  | 1.498秒 | 205.401ms | 0.001ms | 0.002ms | 426.065ms | 591.88ms | 0.002ms | 258.898ms | https://v.youku.com/v_show/id_XNjUxODQ1MzE1Ng==.html |  |
| 低端影视 | 成功 |  | 5.946秒 | 171.666ms | 0.001ms | 0.001ms | 2.526秒 | 2.988秒 | 0.005ms | 217.88ms | https://pan.quark.cn/s/bb5588471842 |  |
| 修罗 | 成功 |  | 27.542秒 | 7.371ms | 0.001ms | 0.001ms | 2.615秒 | 2.488秒 | 5.108秒 | 1.703秒 | https://v16m-default.akamaized.net/9cdf18b2dd4ad589579d6c41467602aa/862bc9d9/video/tos/alisg/tos-alisg-v-26190a-sg/osERzcA0Kf5u6i4Y2dHBowAgqWAPYjAAkEAmim/ |  |
| 凡客TV | 成功 |  | 18.011秒 | 4.057ms | 0.001ms | 0.001ms | 4.28秒 | 1.712秒 | 7.722秒 | 4.294秒 | https://fktv.me/ysapi/m3u8/p/331cc8bfc3ce3d31f5bf1edba04c2374.m3u8 |  |
| 剧圈圈 | 成功 |  | 29.883秒 | 4.792ms | 0.0ms | 0.0ms | 4.328秒 | 3.524秒 | 16.574秒 | 5.451秒 | https://www.jqqzx.cc/play/62935-3-1.html |  |
| 剧迷 | 成功 |  | 28.527秒 | 5.596ms | 0.001ms | 0.001ms | 2.912秒 | 3.015秒 | 8.275秒 | 4.048秒 | https://img.ruyijx.com/m3u8/Wysg2aVa2rs6dl.m3u8?3hGUfnzSswR6ZUdM4U |  |
| 博看听书 | 成功 |  | 4.443秒 | 4.55ms | 0.001ms | 3.185秒 | 277.211ms | 786.423ms | 0.003ms | 188.864ms | http://audio.bookan.com.cn/video1/audio/20200706001/aache64_133068a2.m4a |  |
| 双星 | 成功 |  | 966.906ms | 4.917ms | 334.962ms | 0.004ms | 188.232ms | 202.113ms | 0.002ms | 236.037ms | https://pan.quark.cn/s/27a0785f1c96 |  |
| 听书 | 成功 |  | 3.265秒 | 10.049ms | 80.397ms | 0.001ms | 181.246ms | 2.586秒 | 301.226ms | 105.357ms | http://audiopay.cos.tx.xmcdn.com/download/1.0.0/storages/b817-audiopay/16/AA/GKwRIaIGGaRGADgE-gEx_hMS-aacv2-48K.m4a?sign=f9c315a648e126d0ab7f7106040a3851&buy_key=FM&token=3144&timestamp=1778540531&duration=453 |  |
| 听友FM | 成功 |  | 22.649秒 | 7.181ms | 0.0ms | 3.163秒 | 4.002秒 | 8.441秒 | 6.856秒 | 177.462ms | https://file.hgeuz.cn/stream/eJwANwDI_wJVZgVKIIrU0ECux-GJ1PSt38ahythCqsH-r9TAQ4rj5F94rOjbQKjk063xyIX2z3hfeGcIHF4BAAD__5DtISY.?ts=1778540149&sign=6ea297eb43289c858e10acd340c27174 |  |
| 四万影视 | 失败 | 未预期异常 | 2.907秒 | 3.811ms | 0.001ms | 0.0ms | 2.901秒 | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='40000.me', port=443): Max retries exceeded with url: /api/maccms?ac=detail&t=20&pg=1&by=time (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1081)'))) |
| 在线之家 | 成功 |  | 10.282秒 | 5.36ms | 0.001ms | 0.0ms | 1.847秒 | 4.792秒 | 3.376秒 | 260.879ms | https://media-sxty-fy-corp.sx3oss.ctyunxs.cn/CORPCLOUD/f076ccf5-a095-45a2-b086-cbf66f4aa40d.mp4?response-content-disposition=attachment%3Bfilename%3D%22%E9%93%81%E8%A1%80%E6%88%98%E5%A3%AB%E6%9D%80%E6%88%AE%E4%B9%8B%E5%9C%B02025HD1080P.mp4%22%3Bfilename*%3DUTF-8%27%27%25E9%2593%2581%25E8%25A1%2580%25E6%2588%2598%25E5%25A3%25AB%25E6%259D%2580%25E6%2588%25AE%25E4%25B9%258B%25E5%259C%25B02025HD1080P.mp4&x-amz-CLIENTNETWORK=UNKNOWN&x-amz-CLOUDTYPEIN=CORP&x-amz-CLIENTTYPEIN=UNKNOWN&Signature=uNX1klCEYGkWcbZAQ%2BC07SJKcto%3D&AWSAccessKeyId=0Lg7dAq3ZfHvePP8DKEU&Expires=1778550636&x-amz-limitrate=102400&response-content-type=video/mp4&x-amz-FSIZE=2183471772&x-amz-UID=10000004591358&x-amz-UFID=31374317010337932 |  |
| 多多 | 成功 |  | 1.786秒 | 4.447ms | 0.001ms | 0.001ms | 518.639ms | 432.01ms | 0.003ms | 830.089ms | https://pan.baidu.com/s/1tCpt9UMVoL9OxQyvpKUYZA?pwd=yyds |  |
| 奕搜 | 失败 | 分类列表 | 9.88秒 | 3.453ms | 0.001ms | 0.001ms | 4.886秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 如意资源 | 成功 |  | 13.366秒 | 3.693ms | 0.001ms | 0.006ms | 6.445秒 | 4.386秒 | 0.004ms | 2.531秒 | https://svip.ryiplay18.com/20260508/6294_cfc8934f/index.m3u8 |  |
| 布布影视 | 成功 |  | 10.123秒 | 5.125ms | 0.001ms | 0.001ms | 3.42秒 | 2.135秒 | 4.185秒 | 376.226ms | https://c167-obsdaz-ykj-01.obs.dualstack.cidc-rp-2006.joint.cmecloud.cn/1810c8ff2a78456b9348fadfe7ab0fd0086?response-content-disposition=attachment%3B%20filename%2A%3DUTF-8%27%274K.mp4&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20260511T230221Z&X-Amz-SignedHeaders=host&X-Amz-Expires=86400&X-Amz-Credential=AH4RWOMWLEL7ROYSF2S5%2F20260511%2Fcidc-rp-2006%2Fs3%2Faws4_request&t=2&u=1261698636582652615&ot=family&oi=1263000283947275586&f=FibTFWRt8ncqZsYDWQP5LF5BI3oB5_LXK&ext=eyJ1dCI6MX0%3D&X-Amz-Signature=611311c6b4bcfb59dff4e1a6f1cfb4fcff5b22f507675fbdc9226507d94d796a |  |
| 微观短剧 | 成功 |  | 1.722秒 | 3.566ms | 0.013ms | 194.881ms | 321.232ms | 1.082秒 | 0.002ms | 119.971ms | https://tv-video.cdn.drama.9ddm.com/22/A0/22A0BFFF46651CC23355B115F6307653.mp4?timestamp=1778540532&sign=2e13a83d88e58230016edeff726297f5 |  |
| 新韩剧网 | 成功 |  | 9.949秒 | 3.902ms | 0.001ms | 0.0ms | 2.824秒 | 1.753秒 | 1.751秒 | 3.618秒 | https://cdn.yzzy31-play.com/20251216/9033_3613ef1e/index.m3u8 |  |
| 星星短剧 | 成功 |  | 1.259秒 | 3.097ms | 0.001ms | 0.0ms | 423.143ms | 648.832ms | 0.002ms | 182.789ms | https://img.novel.wsljf.xyz/shortPlay-mp4/420424102051841/EvnIm1746774634078/abc6208e-390b-4533-a1a4-b9e5741cc384/540x960/output.m3u8 |  |
| 木偶 | 成功 |  | 5.597秒 | 3.562ms | 0.001ms | 0.0ms | 2.236秒 | 3.091秒 | 0.006ms | 266.164ms | https://115cdn.com/s/swf0al236dh?password=y244 |  |
| 樱花动漫 | 成功 |  | 21.565秒 | 3.679ms | 0.001ms | 0.0ms | 7.452秒 | 4.128秒 | 5.253秒 | 4.728秒 | https://yzzy.play-cdn2.com/20220413/12637_691cf585/index.m3u8 |  |
| 橘子TV | 成功 |  | 22.224秒 | 6.353ms | 4.404秒 | 4.419秒 | 2.747秒 | 2.275秒 | 8.292秒 | 80.363ms | https://ad.kpyy258.com/m3u87/share/7256561/7452333/20260503/185008/1080/index.m3u8?sign=59ff4a18a54d6057714f2f68e2a14a0e&t=1778540553 |  |
| 欧歌 | 成功 |  | 6.963秒 | 3.754ms | 0.001ms | 0.0ms | 4.07秒 | 1.867秒 | 0.007ms | 1.021秒 | https://pan.baidu.com/s/1QrS21UinfBlr6zbUBxFCVA?pwd=8888 |  |
| 河马短剧 | 成功 |  | 3.242秒 | 4.983ms | 0.001ms | 400.598ms | 940.406ms | 1.815秒 | 0.026ms | 80.732ms | https://dzzt-video.cbread.cn/471a00333ac243329c0e59dc4f69288b/6a0394d0/58/5x3/53x4/534x6/53468100014/612428785_1/612428785.720p.narrowv3.mp4 |  |
| 滴答影视 | 成功 |  | 6.418秒 | 3.984ms | 0.001ms | 0.001ms | 3.193秒 | 2.907秒 | 0.004ms | 313.483ms | https://pan.quark.cn/s/98a640e2e3ee |  |
| 潮流APP | 成功 |  | 814.423ms | 3.933ms | 0.003ms | 121.199ms | 125.994ms | 177.789ms | 283.11ms | 101.795ms | http://43.248.100.143:9090/nby/m3u8/getM3u8?name=jx.91by.top&time=1778540541483&url=NBY-e84585334a25c5b49078dfac81549a0b.m3u8 |  |
| 爱奇艺 | 成功 |  | 5.084秒 | 21.517ms | 0.018ms | 3.689秒 | 955.377ms | 228.16ms | 0.001ms | 189.223ms | http://www.iqiyi.com/v_vd55wo89uk.html |  |
| 独播库 | 成功 |  | 9.391秒 | 4.635ms | 0.001ms | 0.001ms | 2.912秒 | 1.832秒 | 1.82秒 | 2.821秒 | https://vid.dbokutv.com/20260421/ppotb62-S71lT2yliZApDBSvkYzBsrmD3fpCJ4nBsHbTcyo5xOy6ejP6DoBJ0nBJ0oCJT1D491HIvjS34/chunklist.m3u8 |  |
| 玩偶哥哥 | 成功 |  | 7.018秒 | 3.629ms | 0.001ms | 0.0ms | 4.019秒 | 1.961秒 | 0.003ms | 1.034秒 | https://pan.baidu.com/s/1Ra4Pgz8mbihw-Bw3TYkv2g?pwd=wogg |  |
| 玩偶聚合 | 成功 |  | 8.483秒 | 20.559ms | 0.001ms | 0.149ms | 3.183秒 | 4.198秒 | 0.002ms | 1.08秒 | https://pan.baidu.com/s/1CvrInDz-4iEEcZzekTr_Ig?pwd=wogg |  |
| 瓜子 | 成功 |  | 13.321秒 | 9.636ms | 0.001ms | 0.02ms | 2.43秒 | 8.595秒 | 2.136秒 | 150.08ms | https://vd.hxcztech.com/fa86868efcd1cc8177ce3d8c23aca0c1/20260512070235/decry/vd/20260311/MjYwZjE1YTRkO/172631/1998_1080/aac/h264/hls/decrypt/index.m3u8 |  |
| 百度短剧 | 成功 |  | 1.638秒 | 3.458ms | 0.001ms | 459.827ms | 222.001ms | 631.527ms | 232.174ms | 88.634ms | http://vd3.bdstatic.com/mda-rh54j6is12ydd0q3/1080p/mv_cae264_backtrack_1080p_normal/1754453773225130912/mda-rh54j6is12ydd0q3.mp4?v_from_s=haokan-ui-video-hna |  |
| 盘Ta | 成功 |  | 1.145秒 | 3.623ms | 0.0ms | 374.015ms | 301.802ms | 302.284ms | 0.024ms | 162.219ms | https://yun.139.com/shareweb/#/w/i/2sUfBKpu5QBqz |  |
| 盘聚 | 成功 |  | 10.404秒 | 4.759ms | 0.001ms | 0.0ms | 3.817秒 | 2.852秒 | 2.805秒 | 925.173ms | https://pan.baidu.com/s/1NiQJW0DJBw8FR_Y1_k8Yig?pwd=ojmk |  |
| 短剧优选 | 成功 |  | 1.686秒 | 31.373ms | 672.684ms | 0.1ms | 492.706ms | 416.13ms | 0.002ms | 72.233ms | https://cdn-vod-playlet.wtzw.com/asset/b936eac78f199fd865afbe3c5b707e7f/play_multi_video/6f7310c287644b7c813ab8e2eb7a4a0c/f1223068052dd7f1bc88718af4b2c0e4.m3u8 |  |
| 短剧网 | 成功 |  | 6.225秒 | 3.448ms | 0.001ms | 0.001ms | 3.324秒 | 1.883秒 | 0.004ms | 1.014秒 | https://pan.baidu.com/s/1xdVrNMic7RtFFefdR3nJCA?pwd=6666 |  |
| 糯米 | 成功 |  | 2.019秒 | 5.018ms | 0.0ms | 502.374ms | 644.789ms | 154.387ms | 317.65ms | 394.541ms | https://vip.123pan.cn/1853039965/dy/东北往事极恶不赦.m3u8 |  |
| 红果短剧 | 失败 | 分类列表 | 391.608ms | 7.274ms | 0.001ms | 0.001ms | 200.697ms | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 网易云音乐 | 失败 | 未预期异常 | 1.162秒 | 4.087ms | 0.001ms | 493.73ms | 469.062ms | 0.004ms | 190.685ms | 0.0ms |  | Expecting value: line 1 column 1 (char 0) |
| 耐视点播 | 失败 | 分类列表 | 9.797秒 | 4.124ms | 0.001ms | 0.0ms | 3.822秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 腾讯视频 | 成功 |  | 1.496秒 | 8.972ms | 0.001ms | 172.461ms | 299.097ms | 808.361ms | 0.002ms | 205.925ms | https://v.qq.com/x/cover/mzc002009g0nh88/w4102d4f4ur.html |  |
| 至臻 | 成功 |  | 4.04秒 | 3.88ms | 0.001ms | 0.001ms | 1.924秒 | 1.884秒 | 0.011ms | 227.649ms | https://pan.quark.cn/s/b3e194803b59 |  |
| 茶杯狐 | 失败 | 地址校验 | 29.562秒 | 5.797ms | 0.0ms | 3.553秒 | 2.216秒 | 2.051秒 | 4.267秒 | 4.463秒 | https://vip.ffzy-video.com/20260407/41096_2b736f73/index.m3u8 | HTTP 403 |
| 虎斑 | 成功 |  | 9.44秒 | 5.632ms | 0.001ms | 0.001ms | 379.694ms | 7.885秒 | 0.009ms | 1.169秒 | https://pan.baidu.com/s/1KEjunCKCT9t2RnJuelg96Q?pwd=9856 |  |
| 蜡笔 | 成功 |  | 6.286秒 | 8.492ms | 0.001ms | 0.001ms | 3.346秒 | 1.857秒 | 0.003ms | 1.074秒 | https://pan.baidu.com/s/1NiPgbk9_FIhSYfmGm-Cqxg?pwd=q5m6 |  |
| 袋鼠影视 | 失败 | 地址校验 | 19.011秒 | 4.745ms | 0.001ms | 0.0ms | 2.174秒 | 1.962秒 | 1.886秒 | 2.577秒 | https://v.lzcdn27.com/20260511/10160_1504c651/index.m3u8 | HTTP 404 |
| 路漫漫 | 成功 |  | 11.152秒 | 4.127ms | 0.001ms | 0.001ms | 2.404秒 | 2.105秒 | 4.535秒 | 2.103秒 | https://www.lmm85.com/play/8054_1_1.html |  |
| 酷我听书 | 成功 |  | 4.878秒 | 4.684ms | 0.0ms | 404.903ms | 90.488ms | 213.544ms | 149.274ms | 87.846ms | http://cz.sycdn.kuwo.cn/1d3f3fa72cec4af1b0dbd96a4a167f44/6a02600b/resource/m1/34/31/3390639861.wma?bitrate$128&format$wma&source$kwplayerhd_ar_4.3.0.8_tianbao_T1A_qirui.apk&type$convert_url_with_sign&user$&loginUid$ |  |
| 酷狗音乐 | 成功 |  | 1.942秒 | 9.798ms | 520.105ms | 309.797ms | 258.675ms | 353.846ms | 337.888ms | 150.336ms | http://fsdg360.tx.kugou.com/202605120702/5e0dfccc534b2ead0022b12ef2e766be/v3/41d8411641d1e9e8c11cc7773ba26be5/yp/p_0_960155/ap1013_us0_mic85f71c379c462618de1399950957c33_pi6101_mx759135799_qu128_s306155770.mp3?ft=car_203559_10049&fts=b05bb02d44717442054bac7624ed9a29&ext=.mp3 |  |
| 金牌 | 成功 |  | 1.981秒 | 3.821ms | 0.001ms | 721.86ms | 256.53ms | 250.189ms | 238.962ms | 508.709ms | https://ppvod011.blbtgg.com/splitOut/20260318/1267932/V20260318194542050871267932/index.m3u8?auth_key=1778540552-e0432097e8ec412eafdae4a52c49a05d-0-580b088bd1959b2ad61b7b4f293563aa |  |
| 闪电 | 成功 |  | 11.845秒 | 7.768ms | 0.001ms | 0.001ms | 5.858秒 | 5.686秒 | 0.008ms | 291.817ms | https://pan.quark.cn/s/8aaa2a68473f |  |
| 飞快TV | 成功 |  | 17.668秒 | 5.832ms | 0.001ms | 0.001ms | 4.984秒 | 5.001秒 | 5.121秒 | 2.555秒 | https://cdn.vvvip-plays33.cc/20260413/11995_c7820797/index.m3u8 |  |
| 魔方APP | 失败 | 首页分类 | 2.284秒 | 5.987ms | 0.001ms | 2.277秒 | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | 分类列表为空 |
| 麦田影院 | 失败 | 未预期异常 | 2.049秒 | 4.668ms | 0.001ms | 0.001ms | 2.042秒 | 0.0ms | 0.0ms | 0.0ms |  | ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| 黑猫APP | 失败 | 地址校验 | 14.212秒 | 4.51ms | 0.001ms | 2.165秒 | 1.981秒 | 829.849ms | 0.009ms | 2.613秒 | https://v10.ppqrrs.com/wjv10/202605/11/JGqJmrkWkG88/video/index.m3u8 | HTTP 403 |
