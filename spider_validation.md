# 爬虫校验报告

- 生成时间: 2026-05-12T10:03:50+08:00
- 并发线程数: 16
- 总耗时(ms): 151.886秒
- 总数: 69
- 成功: 52
- 失败: 17

## 阶段失败统计

| 阶段 | 数量 |
| --- | ---: |
| 模块加载 | 0 |
| 初始化 | 0 |
| 首页分类 | 1 |
| 分类列表 | 4 |
| 视频详情 | 0 |
| 播放地址 | 1 |
| 地址校验 | 5 |
| 未预期异常 | 6 |

## 明细结果

| 爬虫 | 状态 | 失败阶段 | 总耗时 | 模块加载 | 初始化 | 首页分类 | 分类列表 | 视频详情 | 播放地址 | 地址校验 | 返回地址 | 错误信息 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 4K指南 | 成功 |  | 4.027秒 | 186.451ms | 0.001ms | 0.003ms | 2.506秒 | 1.076秒 | 0.003ms | 256.923ms | https://pan.xunlei.com/s/VOsM-4grxeaeMV65z_HmIk5tA1?pwd=g3hz |  |
| AAZ音乐 | 失败 | 未预期异常 | 10.176秒 | 125.431ms | 0.001ms | 10.049秒 | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='www.aaz.cx', port=443): Read timed out. (read timeout=10) |
| PPnix | 成功 |  | 3.346秒 | 255.432ms | 0.001ms | 0.001ms | 1.238秒 | 1.155秒 | 0.012ms | 695.806ms | https://www.ppnix.com/info/m3u8/8140/1080P.m3u8 |  |
| QQ音乐 | 成功 |  | 2.015秒 | 154.853ms | 0.008ms | 0.002ms | 584.014ms | 647.283ms | 555.748ms | 72.255ms | https://isure.stream.qqmusic.qq.com/F0000014qLXa1JrJ11.flac?guid=122eb1e275b31a002cb8d77b34499c2a&vkey=BDF40EEB64CBFFFF758290AC14D557C6336920D473B07E94E388DE234C709FEDB5E2DCF57C028285AD3C75F8127672484BF06217E5F71E82__v2b9abc6c&uin=1152921504846230218&fromtag=119114&redirect=1 |  |
| libvio | 失败 | 分类列表 | 3.018秒 | 222.152ms | 0.001ms | 0.001ms | 817.988ms | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| youknow | 成功 |  | 13.323秒 | 158.982ms | 0.001ms | 0.0ms | 2.536秒 | 2.022秒 | 2.08秒 | 6.525秒 | https://vip.dytt-cinema.com/20250217/4114_ab24cd2b/index.m3u8 |  |
| 不太灵 | 失败 | 播放地址 | 9.548秒 | 170.859ms | 0.001ms | 2.12秒 | 1.08秒 | 3.962秒 | 0.006ms | 0.0ms |  | playerContent 未返回播放地址 |
| 世纪音乐 | 失败 | 地址校验 | 1.234秒 | 167.435ms | 0.001ms | 254.753ms | 0.006ms | 139.795ms | 0.004ms | 163.365ms | https://www.4c44.com/data/down.php?ac=music&id=hkwyytdecc | HTTP 403 |
| 两个BT | 成功 |  | 9.138秒 | 211.309ms | 0.001ms | 0.0ms | 1.092秒 | 2.41秒 | 2.041秒 | 3.383秒 | https://zijieapi.douyinbyte.com/m3u8/4408476d5cd42f3806ad8b3a905d5818.m3u8 |  |
| 乌云影视 | 成功 |  | 7.955秒 | 200.397ms | 0.001ms | 1.079秒 | 964.639ms | 2.709秒 | 0.018ms | 3.002秒 | https://d1jdnmkc1n5cn4.cloudfront.net/gen_overseas/https://s2.bfllvip.com/video/yanxiaxing/a6ef854c0c1f/index.m3u8 |  |
| 乐兔 | 失败 | 未预期异常 | 10.232秒 | 186.859ms | 0.001ms | 0.001ms | 10.043秒 | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='www.letu.me', port=443): Read timed out. (read timeout=10) |
| 二小 | 成功 |  | 3.757秒 | 161.884ms | 0.001ms | 0.001ms | 2.597秒 | 787.477ms | 0.009ms | 210.106ms | https://pan.quark.cn/s/b3e194803b59 |  |
| 人人电影 | 失败 | 分类列表 | 3.379秒 | 211.941ms | 0.001ms | 0.001ms | 1.511秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 人人视频 | 失败 | 地址校验 | 2.716秒 | 175.604ms | 0.001ms | 266.372ms | 270.792ms | 278.508ms | 390.275ms | 209.542ms | https://tfvt0grhdgmt1gc41hcttghzdnptz.ourdvsssvip.com:20443/ws-302.bwcgee.cn/307ba6dcef6871ef85774531959c0402/67389eb6001c4a1e9b1f2f7ca2a82dc1-1b1785a818fc693827ab9628d26d600b-ld.mp4?key=12e9da0fd1ba0cf141625008e93a6aeb&time=1778565832987&clientType=web_pc&clientVersion=1.0.0&parseUsage=PLAY&uid=0&rk=8142f523cecc48f9961f60ad6cc299f0&hevc=false&seasonId=51705&wsiphost=ipdbme&wsrid_tag=6a028a89_PS-KWE-01jPi72_22079-1495-s1t1778551433100&x-mamba-business-label=13679&redirect_cnt=0&ip_type=0&wshc=C&requery=0 | HTTP 403 |
| 优酷 | 成功 |  | 1.541秒 | 203.063ms | 0.001ms | 0.001ms | 408.742ms | 635.813ms | 0.002ms | 290.121ms | https://v.youku.com/v_show/id_XNjUxODQ1MzE1Ng==.html |  |
| 低端影视 | 成功 |  | 4.71秒 | 210.91ms | 0.001ms | 0.001ms | 2.524秒 | 1.802秒 | 0.006ms | 166.788ms | https://pan.quark.cn/s/bb5588471842 |  |
| 修罗 | 成功 |  | 31.338秒 | 7.781ms | 0.001ms | 0.001ms | 2.609秒 | 3.847秒 | 3.959秒 | 2.882秒 | https://v16m-default.akamaized.net/9cdf18b2dd4ad589579d6c41467602aa/862bc9d9/video/tos/alisg/tos-alisg-v-26190a-sg/osERzcA0Kf5u6i4Y2dHBowAgqWAPYjAAkEAmim/ |  |
| 凡客TV | 成功 |  | 19.787秒 | 4.673ms | 0.0ms | 0.001ms | 2.274秒 | 1.536秒 | 11.372秒 | 4.6秒 | https://fktv.me/ysapi/m3u8/p/e05077c961543deb194d3a9bac7a8885.m3u8 |  |
| 剧圈圈 | 成功 |  | 26.83秒 | 4.792ms | 0.0ms | 0.0ms | 2.401秒 | 1.411秒 | 16.797秒 | 6.217秒 | https://www.jqqzx.cc/play/62945-3-1.html |  |
| 剧迷 | 成功 |  | 25.642秒 | 4.611ms | 0.001ms | 0.001ms | 2.156秒 | 3.631秒 | 7.176秒 | 4.026秒 | https://img.ruyijx.com/m3u8/i6XqoumxZDP7X9.m3u8?jHy3Rg4wQUSViZDhIq |  |
| 博看听书 | 成功 |  | 4.421秒 | 3.883ms | 0.0ms | 3.171秒 | 273.304ms | 778.857ms | 0.002ms | 193.248ms | http://audio.bookan.com.cn/video1/audio/20200706001/aache64_133068a2.m4a |  |
| 双星 | 成功 |  | 982.597ms | 7.075ms | 396.45ms | 0.003ms | 202.948ms | 197.798ms | 0.002ms | 177.66ms | https://pan.quark.cn/s/27a0785f1c96 |  |
| 听书 | 成功 |  | 3.533秒 | 6.042ms | 80.39ms | 0.001ms | 195.041ms | 2.864秒 | 310.872ms | 75.724ms | http://audiopay.cos.tx.xmcdn.com/download/1.0.0/storages/b817-audiopay/16/AA/GKwRIaIGGaRGADgE-gEx_hMS-aacv2-48K.m4a?sign=24f8198a568fc309632a43eb960a68a1&buy_key=FM&token=6776&timestamp=1778551437&duration=453 |  |
| 听友FM | 成功 |  | 12.28秒 | 9.304ms | 0.0ms | 1.567秒 | 1.261秒 | 5.086秒 | 4.182秒 | 173.827ms | https://file.hgeuz.cn/stream/eJwANwDI_wJVZgVKIIrU0ECux-GJ1PSt38ahythCqsH-r9TAQ4rj5F94rOjbQKjk063xyIX2z3hfeGcIHF4BAAD__5DtISY.?ts=1778548641&sign=32a10bccb932dbbfb728da19284061b2 |  |
| 四万影视 | 失败 | 未预期异常 | 867.423ms | 3.8ms | 0.0ms | 0.001ms | 860.151ms | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='40000.me', port=443): Max retries exceeded with url: /api/maccms?ac=detail&t=20&pg=1&by=time (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1081)'))) |
| 在线之家 | 成功 |  | 8.299秒 | 6.387ms | 0.0ms | 0.001ms | 853.583ms | 2.694秒 | 4.499秒 | 244.821ms | https://media-sxty-fy-corp.sx3oss.ctyunxs.cn/CORPCLOUD/f076ccf5-a095-45a2-b086-cbf66f4aa40d.mp4?response-content-disposition=attachment%3Bfilename%3D%22%E9%93%81%E8%A1%80%E6%88%98%E5%A3%AB%E6%9D%80%E6%88%AE%E4%B9%8B%E5%9C%B02025HD1080P.mp4%22%3Bfilename*%3DUTF-8%27%27%25E9%2593%2581%25E8%25A1%2580%25E6%2588%2598%25E5%25A3%25AB%25E6%259D%2580%25E6%2588%25AE%25E4%25B9%258B%25E5%259C%25B02025HD1080P.mp4&x-amz-CLIENTNETWORK=UNKNOWN&x-amz-CLOUDTYPEIN=CORP&x-amz-CLIENTTYPEIN=UNKNOWN&Signature=IM2Dw0Y7UxZh3AzEDoZVSjA7RIY%3D&AWSAccessKeyId=0Lg7dAq3ZfHvePP8DKEU&Expires=1778562015&x-amz-limitrate=102400&response-content-type=video/mp4&x-amz-FSIZE=2183471772&x-amz-UID=10000004591358&x-amz-UFID=31374317010337932 |  |
| 多多 | 成功 |  | 1.95秒 | 6.047ms | 0.001ms | 0.0ms | 515.353ms | 478.13ms | 0.003ms | 950.091ms | https://pan.baidu.com/s/1tCpt9UMVoL9OxQyvpKUYZA?pwd=yyds |  |
| 奕搜 | 成功 |  | 6.521秒 | 4.391ms | 0.001ms | 0.0ms | 1.941秒 | 4.395秒 | 0.027ms | 180.696ms | https://pan.quark.cn/s/e5345bdd71f6 |  |
| 如意资源 | 成功 |  | 17.525秒 | 3.692ms | 0.001ms | 0.005ms | 10.489秒 | 2.507秒 | 0.005ms | 4.524秒 | https://svip.ryiplay18.com/20260508/6294_cfc8934f/index.m3u8 |  |
| 布布影视 | 成功 |  | 7.242秒 | 9.5ms | 0.001ms | 0.001ms | 2.305秒 | 2.084秒 | 2.448秒 | 394.674ms | https://c167-obsdaz-ykj-01.obs.dualstack.cidc-rp-2006.joint.cmecloud.cn/1810c8ff2a78456b9348fadfe7ab0fd0086?response-content-disposition=attachment%3B%20filename%2A%3DUTF-8%27%274K.mp4&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20260512T015933Z&X-Amz-SignedHeaders=host&X-Amz-Expires=86400&X-Amz-Credential=AH4RWOMWLEL7ROYSF2S5%2F20260512%2Fcidc-rp-2006%2Fs3%2Faws4_request&t=2&u=1261698636582652615&ot=family&oi=1263000283947275586&f=FibTFWRt8ncqZsYDWQP5LF5BI3oB5_LXK&ext=eyJ1dCI6MX0%3D&X-Amz-Signature=41b73f798d3b2b3b846a28fc9e37449d1d0d2fe3c518a89fe2ce9b8f1fc5b41f |  |
| 微观短剧 | 成功 |  | 1.013秒 | 3.314ms | 0.018ms | 211.093ms | 265.244ms | 355.989ms | 0.002ms | 177.206ms | https://tv-video.cdn.drama.9ddm.com/22/A0/22A0BFFF46651CC23355B115F6307653.mp4?timestamp=1778551438&sign=c7dd312c34760d955cf6f3648e480888 |  |
| 新韩剧网 | 成功 |  | 11.956秒 | 4.093ms | 0.001ms | 0.0ms | 1.823秒 | 3.783秒 | 1.772秒 | 4.574秒 | https://player.yzzyvip-35.com/20260331/3348_333cb763/index.m3u8 |  |
| 星星短剧 | 成功 |  | 1.231秒 | 3.803ms | 0.001ms | 0.0ms | 418.644ms | 649.975ms | 0.002ms | 158.307ms | https://img.novel.wsljf.xyz/shortPlay-mp4/420424102051841/EvnIm1746774634078/abc6208e-390b-4533-a1a4-b9e5741cc384/540x960/output.m3u8 |  |
| 木偶 | 成功 |  | 4.533秒 | 6.013ms | 0.001ms | 0.001ms | 2.292秒 | 1.967秒 | 0.009ms | 267.29ms | https://115cdn.com/s/swf0al236dh?password=y244 |  |
| 樱花动漫 | 失败 | 地址校验 | 45.075秒 | 3.879ms | 0.001ms | 0.0ms | 4.108秒 | 4.106秒 | 4.289秒 | 2.665秒 | https://v.lzcdn27.com/20260407/8292_3aa0f692/index.m3u8 | HTTP 404 |
| 橘子TV | 成功 |  | 22.921秒 | 4.268ms | 4.516秒 | 4.974秒 | 2.401秒 | 2.441秒 | 8.427秒 | 157.539ms | https://tt0923.abc7722.com/m3u87/share/7256561/7452333/20260503/185008/1080/index.m3u8?sign=7b7faf8461b3484d1adaf171c68e80da&t=1778551460 |  |
| 欧歌 | 成功 |  | 5.639秒 | 3.899ms | 0.001ms | 0.0ms | 2.292秒 | 2.057秒 | 0.008ms | 1.285秒 | https://pan.baidu.com/s/1QrS21UinfBlr6zbUBxFCVA?pwd=8888 |  |
| 河马短剧 | 成功 |  | 2.875秒 | 5.151ms | 0.001ms | 718.708ms | 657.19ms | 1.357秒 | 0.022ms | 135.948ms | https://dzzt-video.cbread.cn/803d4ae8df7cd3e4bad95489e43eaf8b/6a03cd10/58/5x3/53x4/534x6/53468100014/612428785_1/612428785.720p.narrowv3.mp4 |  |
| 滴答影视 | 成功 |  | 6.293秒 | 4.145ms | 0.001ms | 0.001ms | 4.257秒 | 1.856秒 | 0.003ms | 176.184ms | https://pan.quark.cn/s/98a640e2e3ee |  |
| 潮流APP | 成功 |  | 807.93ms | 8.147ms | 0.003ms | 120.063ms | 135.899ms | 154.628ms | 285.727ms | 103.013ms | http://43.248.100.143:9090/nby/m3u8/getM3u8?name=jx.91by.top&time=1778551443918&url=NBY-e84585334a25c5b49078dfac81549a0b.m3u8 |  |
| 爱奇艺 | 成功 |  | 4.525秒 | 11.895ms | 0.043ms | 2.958秒 | 1.059秒 | 203.982ms | 0.001ms | 292.254ms | http://www.iqiyi.com/v_vd55wo89uk.html |  |
| 独播库 | 成功 |  | 9.379秒 | 4.585ms | 0.001ms | 0.0ms | 1.834秒 | 3.897秒 | 1.867秒 | 1.775秒 | https://vid.dbokutv.com/20260402/ppotb62-S71lT2yliZApDBSvkYzBsrmD3fpCJ4nBtHsRsGlR7XgBNTjUMjaQ79wBJ0nBJ0mGaGoCpKpHYvjS34/chunklist.m3u8 |  |
| 玩偶哥哥 | 成功 |  | 12.75秒 | 3.565ms | 0.001ms | 0.0ms | 4.013秒 | 3.975秒 | 0.003ms | 4.758秒 | https://pan.baidu.com/s/1Ra4Pgz8mbihw-Bw3TYkv2g?pwd=wogg |  |
| 玩偶聚合 | 成功 |  | 6.559秒 | 7.654ms | 0.001ms | 0.087ms | 3.476秒 | 2.123秒 | 0.002ms | 951.853ms | https://pan.baidu.com/s/1CvrInDz-4iEEcZzekTr_Ig?pwd=wogg |  |
| 瓜子 | 成功 |  | 10.312秒 | 6.316ms | 0.001ms | 0.051ms | 4.204秒 | 4.086秒 | 1.828秒 | 185.813ms | https://vd.hxcztech.com/da672e50d2bcbbd8a64880ae6c33479c/20260512100414/decry/vd/20260311/MjYwZjE1YTRkO/172631/1998_1080/aac/h264/hls/decrypt/index.m3u8 |  |
| 百度短剧 | 成功 |  | 1.686秒 | 3.326ms | 0.0ms | 458.559ms | 234.07ms | 546.992ms | 251.875ms | 190.994ms | http://vd3.bdstatic.com/mda-rh54j6is12ydd0q3/1080p/mv_cae264_backtrack_1080p_normal/1754453773225130912/mda-rh54j6is12ydd0q3.mp4?v_from_s=haokan-ui-video-hna |  |
| 盘Ta | 成功 |  | 1.188秒 | 8.327ms | 0.001ms | 378.118ms | 274.459ms | 313.628ms | 0.019ms | 213.076ms | https://yun.139.com/shareweb/#/w/i/2sUfBKpu5QBqz |  |
| 盘聚 | 成功 |  | 11.964秒 | 5.293ms | 0.001ms | 0.001ms | 3.847秒 | 2.87秒 | 4.136秒 | 1.105秒 | https://pan.baidu.com/s/1NiQJW0DJBw8FR_Y1_k8Yig?pwd=ojmk |  |
| 短剧优选 | 成功 |  | 2.183秒 | 19.685ms | 770.814ms | 0.111ms | 680.39ms | 625.653ms | 0.001ms | 85.683ms | https://cdn-vod-playlet.wtzw.com/asset/b936eac78f199fd865afbe3c5b707e7f/play_multi_video/6f7310c287644b7c813ab8e2eb7a4a0c/f1223068052dd7f1bc88718af4b2c0e4.m3u8 |  |
| 短剧网 | 成功 |  | 8.477秒 | 3.434ms | 0.001ms | 0.0ms | 4.674秒 | 2.343秒 | 0.004ms | 1.456秒 | https://pan.baidu.com/s/1l9EzQI4B-BekE_FUMPLxQg?pwd=6666 |  |
| 糯米 | 成功 |  | 1.852秒 | 5.341ms | 0.001ms | 243.659ms | 689.398ms | 167.645ms | 334.274ms | 411.107ms | https://vip.123pan.cn/1853039965/dy/东北往事极恶不赦.m3u8 |  |
| 红果短剧 | 失败 | 分类列表 | 393.844ms | 3.517ms | 0.0ms | 0.001ms | 185.892ms | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 网易云音乐 | 失败 | 未预期异常 | 132.2秒 | 3.669ms | 0.002ms | 413.149ms | 131.779秒 | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='music.163.com', port=443): Max retries exceeded with url: /discover/toplist?id=19723756 (Caused by ConnectTimeoutError(<HTTPSConnection(host='music.163.com', port=443) at 0x74f9c6c69a90>, 'Connection to music.163.com timed out. (connect timeout=None)')) |
| 耐视点播 | 失败 | 分类列表 | 11.071秒 | 5.458ms | 0.001ms | 0.001ms | 2.857秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 腾讯视频 | 成功 |  | 3.862秒 | 5.356ms | 0.001ms | 1.533秒 | 283.677ms | 1.335秒 | 0.003ms | 704.862ms | https://v.qq.com/x/cover/mzc002009g0nh88/w4102d4f4ur.html |  |
| 至臻 | 成功 |  | 10.179秒 | 3.546ms | 0.001ms | 0.0ms | 5.402秒 | 4.539秒 | 0.006ms | 234.101ms | https://pan.quark.cn/s/b3e194803b59 |  |
| 茶杯狐 | 失败 | 地址校验 | 33.482秒 | 5.974ms | 0.001ms | 2.385秒 | 2.253秒 | 2.146秒 | 4.453秒 | 5.772秒 | https://vip.ffzy-play10.com/20260512/66220_f16f5e95/index.m3u8 | HTTP 403 |
| 虎斑 | 失败 | 未预期异常 | 11.959秒 | 6.892ms | 0.001ms | 0.001ms | 1.819秒 | 10.132秒 | 0.0ms | 0.0ms |  | HTTPConnectionPool(host='109.244.63.150', port=16969): Read timed out. (read timeout=10) |
| 蜡笔 | 成功 |  | 6.871秒 | 4.354ms | 0.001ms | 0.0ms | 4.342秒 | 845.731ms | 0.003ms | 1.678秒 | https://pan.baidu.com/s/1NiPgbk9_FIhSYfmGm-Cqxg?pwd=q5m6 |  |
| 袋鼠影视 | 失败 | 地址校验 | 23.599秒 | 6.95ms | 0.001ms | 0.001ms | 2.298秒 | 2.021秒 | 2.319秒 | 2.992秒 | https://vip.dytt-see.com/20260512/38394_9700420b/index.m3u8 | HTTP 403 |
| 路漫漫 | 成功 |  | 18.51秒 | 4.099ms | 0.0ms | 0.0ms | 4.647秒 | 4.26秒 | 6.459秒 | 3.14秒 | https://www.lmm85.com/play/8054_1_1.html |  |
| 酷我听书 | 成功 |  | 4.858秒 | 4.927ms | 0.0ms | 369.262ms | 97.53ms | 218.07ms | 153.351ms | 129.286ms | http://cz.sycdn.kuwo.cn/ac5ba952c68df68da9f797aa4579a583/6a028aa5/resource/m1/34/31/3390639861.wma?bitrate$128&format$wma&source$kwplayerhd_ar_4.3.0.8_tianbao_T1A_qirui.apk&type$convert_url_with_sign&user$&loginUid$ |  |
| 酷狗音乐 | 成功 |  | 1.987秒 | 7.269ms | 537.449ms | 343.543ms | 260.136ms | 331.74ms | 396.94ms | 108.718ms | http://fsdg360.tx.kugou.com/202605121004/3199a0b72eb8487cf4a69de39e9f57c8/v3/f70b0985663497d511563222d039ced2/yp/p_0_960127/ap1013_us0_mic85f71c379c462618de1399950957c33_pi6101_mx618756441_qu128_s1135599346.mp3?ft=car_203559_10049&fts=b05bb02d44717442054bac7624ed9a29&ext=.mp3 |  |
| 金牌 | 成功 |  | 1.89秒 | 3.978ms | 0.001ms | 914.028ms | 259.824ms | 237.769ms | 232.632ms | 241.337ms | https://ppvod01.kqgfbs.com/splitOut/20260318/1267932/V20260318194542050871267932/index.m3u8?t=6a02b4d4&whip=222.210.194.201&sign=a371eef37f4755dc80b71e6c2d87e533b1ad4431 |  |
| 闪电 | 成功 |  | 13.004秒 | 5.168ms | 0.001ms | 0.001ms | 7.123秒 | 5.636秒 | 0.011ms | 239.748ms | https://pan.quark.cn/s/8aaa2a68473f |  |
| 飞快TV | 成功 |  | 20.943秒 | 6.912ms | 0.001ms | 0.001ms | 7.598秒 | 5.571秒 | 5.251秒 | 2.515秒 | https://cdn.vvvip-plays33.cc/20260413/11995_c7820797/index.m3u8 |  |
| 魔方APP | 失败 | 首页分类 | 2.136秒 | 5.768ms | 0.001ms | 2.13秒 | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | 分类列表为空 |
| 麦田影院 | 失败 | 未预期异常 | 2.934秒 | 4.316ms | 0.001ms | 0.001ms | 2.925秒 | 0.0ms | 0.0ms | 0.0ms |  | ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| 黑猫APP | 成功 |  | 11.351秒 | 4.896ms | 0.001ms | 4.717秒 | 2.24秒 | 2.028秒 | 2.204秒 | 156.336ms | https://v3-dy-o.zjcdn.com/32472555eb1cedeab73d85f913ccfca9/6a02e690/video/tos/cn/tos-cn-v-5f73e7/o4DmBvfrySVPpFCaE36BH4DqEoIAeISg1w9pgJ/ |  |
