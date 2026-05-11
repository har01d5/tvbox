# 爬虫校验报告

- 生成时间: 2026-05-11T17:18:33+08:00
- 并发线程数: 16
- 总耗时(ms): 113713.185
- 总数: 80
- 成功: 49
- 失败: 31

## 阶段失败统计

| 阶段 | 数量 |
| --- | ---: |
| 模块加载 | 0 |
| 初始化 | 0 |
| 首页分类 | 1 |
| 分类列表 | 8 |
| 视频详情 | 2 |
| 播放地址 | 1 |
| 地址校验 | 11 |
| 未预期异常 | 8 |

## 明细结果

| 爬虫 | 状态 | 失败阶段 | 总耗时 | 模块加载 | 初始化 | 首页分类 | 分类列表 | 视频详情 | 播放地址 | 地址校验 | 返回地址 | 错误信息 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 4K指南 | 成功 |  | 5096.975 | 20.286 | 0.001 | 0.001 | 2651.196 | 2211.211 | 0.004 | 212.804 | https://pan.quark.cn/s/e0726c4989dc |  |
| AAZ音乐 | 失败 | 未预期异常 | 10064.188 | 21.505 | 0.001 | 10037.505 | 0.0 | 0.0 | 0.0 | 0.0 |  | HTTPSConnectionPool(host='www.aaz.cx', port=443): Read timed out. (read timeout=10) |
| Atvp | 失败 | 未预期异常 | 89.728 | 87.849 | 0.005 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |  | Atvp source is empty |
| PPnix | 成功 |  | 6678.435 | 68.788 | 0.0 | 0.001 | 2315.792 | 2587.129 | 0.009 | 1705.982 | https://www.ppnix.com/info/m3u8/8138/1080P.m3u8 |  |
| QQ音乐 | 失败 | 地址校验 | 7294.602 | 24.958 | 0.01 | 0.004 | 925.84 | 889.688 | 356.223 | 5096.391 | https://isure.stream.qqmusic.qq.com/F0000040rOp00lZYHC.flac?guid=937a68440e991cc92362d06118a0492e&vkey=CA32E307024DDCE41094CB678C26E38D6E253A6C717DE40864AEFA7E2B220C35D2EF256CA69424C393E9CC5853369D899CB6427C3DDDD65C__v2b9a8921&uin=1152921504846230218&fromtag=119114&redirect=1 | HTTPSConnectionPool(host='isure.stream.qqmusic.qq.com', port=443): Read timed out. (read timeout=5) |
| UVod | 失败 | 地址校验 | 14139.019 | 84.294 | 2092.936 | 3332.08 | 2859.65 | 1960.722 | 2031.86 | 1776.136 | https://file-endpoint33.oledsa.com/content/dy-ljwl-shd-20260509-01.mp4/index.m3u8?st=ObWElss8Zg1rOx2ENQcyAQ&e=1778505525 | HTTPSConnectionPool(host='file-endpoint33.oledsa.com', port=443): Max retries exceeded with url: /content/dy-ljwl-shd-20260509-01.mp4/index.m3u8?st=ObWElss8Zg1rOx2ENQcyAQ&e=1778505525 (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)'))) |
| libvio | 失败 | 分类列表 | 1975.524 | 20.209 | 0.001 | 0.001 | 1955.01 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| youknow | 成功 |  | 11304.781 | 19.727 | 0.001 | 0.001 | 3040.21 | 2562.492 | 2906.026 | 2774.777 | https://vip.dytt-tvs.com/20260405/15441_95ce3f8d/index.m3u8 |  |
| youtube | 失败 | 分类列表 | 2737.494 | 20.784 | 0.003 | 0.021 | 2714.591 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| 七味 | 成功 |  | 113707.036 | 17.346 | 0.001 | 0.001 | 2430.342 | 2339.188 | 107127.908 | 1790.299 | https://www.pcmp4.com/py/94740-3-1.html |  |
| 不太灵 | 失败 | 播放地址 | 9495.707 | 17.773 | 0.001 | 2942.341 | 3865.385 | 2668.435 | 0.017 | 0.0 |  | playerContent 未返回播放地址 |
| 世纪音乐 | 失败 | 地址校验 | 823.423 | 19.609 | 0.001 | 282.307 | 164.444 | 158.36 | 0.012 | 192.854 | https://www.4c44.com/data/down.php?ac=music&id=cwdkeyncc | HTTP 403 |
| 两个BT | 成功 |  | 10866.582 | 25.18 | 0.001 | 0.001 | 2153.047 | 1968.833 | 3779.655 | 2937.794 | https://zijieapi.douyinbyte.com/m3u8/dd0ca2ca11fcbf34e0a0d769ad4f7180.m3u8 |  |
| 乌云影视 | 成功 |  | 13294.848 | 21.344 | 0.001 | 1930.965 | 1936.543 | 5106.647 | 0.025 | 4297.282 | https://d1jdnmkc1n5cn4.cloudfront.net/gen_overseas/https://s2.bfllvip.com/video/yanxiaxing/a6ef854c0c1f/index.m3u8 |  |
| 乐兔 | 失败 | 未预期异常 | 10091.537 | 17.578 | 0.001 | 0.001 | 10068.401 | 0.0 | 0.0 | 0.0 |  | HTTPSConnectionPool(host='www.letu.me', port=443): Read timed out. (read timeout=10) |
| 二小 | 成功 |  | 6355.963 | 14.537 | 0.001 | 0.001 | 4285.824 | 1826.348 | 0.012 | 226.526 | https://pan.quark.cn/s/b3e194803b59 |  |
| 人人电影 | 失败 | 分类列表 | 2030.057 | 0.312 | 0.001 | 0.001 | 2029.53 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| 人人视频 | 失败 | 地址校验 | 1324.231 | 0.938 | 0.002 | 185.43 | 255.019 | 255.222 | 431.597 | 195.226 | https://a3fkpcuj0vitsro.302.fledgecloud.com:56782/zj-302-cdn.bwcgee.cn/60b815c142c671f1ac975017e1f90402/30ffc804ae454cdaa23c4518d492908d-0e6b5348788a46aeb1399e154ae316e5-ld.mp4?auth_key=1778505515-c27d5247ecabfc2f3924fb6b39c7e6e1-0-56c66b0fa0f1bf6a0bef164fc4d4aa02&clientType=web_pc&clientVersion=1.0.0&parseUsage=PLAY&uid=0&rk=935a2c5f6d634d3aaee9d40e0e657443&hevc=false&seasonId=57181 | HTTP 403 |
| 优酷 | 成功 |  | 1166.376 | 0.371 | 0.001 | 0.001 | 300.197 | 600.93 | 0.002 | 264.554 | https://v.youku.com/v_show/id_XNjUxODQ1MzE1Ng==.html |  |
| 低端影视 | 成功 |  | 5668.527 | 0.298 | 0.001 | 0.001 | 2607.753 | 2918.807 | 0.007 | 141.355 | https://hn.bfvvs.com/play/eXDLzQVe/index.m3u8 |  |
| 修罗 | 失败 | 地址校验 | 14692.185 | 0.399 | 0.0 | 0.001 | 4487.286 | 1737.243 | 4620.384 | 3845.886 | https://v.xlys.ltd.ua/obj/84195C26011E2CEAA2C7525CD7DD72B89A9FC40150564B60D606915002E62382 | HTTP 403 |
| 凡客TV | 成功 |  | 15261.822 | 0.276 | 0.0 | 0.0 | 2605.818 | 2413.079 | 5880.585 | 4361.654 | https://fktv.me/ysapi/m3u8/p/59a97924eaa4a4151f13a9dd67ce4eb5.m3u8 |  |
| 剧圈圈 | 成功 |  | 21292.609 | 0.308 | 0.0 | 0.0 | 3633.974 | 3684.359 | 10506.432 | 3466.652 | https://www.jqqzx.cc/play/62945-3-1.html |  |
| 剧迷 | 失败 | 地址校验 | 10455.824 | 0.488 | 0.001 | 0.001 | 2193.185 | 2289.401 | 2198.259 | 3773.298 | https://vip.dytt-see.com/20260505/36518_39a596c5/index.m3u8 | HTTP 403 |
| 博看听书 | 成功 |  | 4374.021 | 0.315 | 0.001 | 3198.461 | 298.251 | 798.841 | 0.005 | 77.55 | http://audio.bookan.com.cn/video1/audio/20200706001/aache64_133068a2.m4a |  |
| 厂长资源 | 失败 | 分类列表 | 7886.033 | 0.81 | 0.105 | 0.002 | 7884.744 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| 双星 | 失败 | 未预期异常 | 15621.121 | 0.21 | 409.321 | 0.006 | 192.49 | 15016.331 | 0.0 | 0.0 |  | HTTPSConnectionPool(host='1.star2.cn', port=443): Max retries exceeded with url: /ju/10345.html (Caused by ConnectTimeoutError(<HTTPSConnection(host='1.star2.cn', port=443) at 0x7e9ae9cff890>, 'Connection to 1.star2.cn timed out. (connect timeout=15)')) |
| 听书 | 成功 |  | 2351.859 | 0.245 | 78.969 | 0.001 | 194.909 | 490.627 | 1439.985 | 146.42 | http://audiopay.cos.tx.xmcdn.com/download/1.0.0/storages/b817-audiopay/16/AA/GKwRIaIGGaRGADgE-gEx_hMS-aacv2-48K.m4a?sign=49ad5f9118fba7428c6ebf92bc9fe9e8&buy_key=FM&token=6751&timestamp=1778491123&duration=453 |  |
| 听友FM | 成功 |  | 12901.94 | 3.537 | 0.002 | 3034.059 | 2335.989 | 2804.054 | 4540.003 | 183.104 | https://file.hgeuz.cn/stream/eJwANwDI_wJVZgVKIIrU0ECux-GJ1PSt38ahythCqsH-r9TAQ4rj5F94rOjbQKjk063xyIX2z3hfeGcIHF4BAAD__5DtISY.?ts=1778488205&sign=625c3a14e1a6c8df8d4d35663d542452 |  |
| 四万影视 | 失败 | 未预期异常 | 1826.11 | 0.425 | 0.001 | 0.001 | 1823.877 | 0.0 | 0.0 | 0.0 |  | HTTPSConnectionPool(host='40000.me', port=443): Max retries exceeded with url: /api/maccms?ac=detail&t=20&pg=1&by=time (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1081)'))) |
| 在线之家 | 成功 |  | 8475.455 | 0.698 | 0.002 | 0.002 | 1884.669 | 4077.169 | 2264.544 | 247.591 | https://media-sxty-fy-corp.sx3oss.ctyunxs.cn/CORPCLOUD/f076ccf5-a095-45a2-b086-cbf66f4aa40d.mp4?response-content-disposition=attachment%3Bfilename%3D%22%E9%93%81%E8%A1%80%E6%88%98%E5%A3%AB%E6%9D%80%E6%88%AE%E4%B9%8B%E5%9C%B02025HD1080P.mp4%22%3Bfilename*%3DUTF-8%27%27%25E9%2593%2581%25E8%25A1%2580%25E6%2588%2598%25E5%25A3%25AB%25E6%259D%2580%25E6%2588%25AE%25E4%25B9%258B%25E5%259C%25B02025HD1080P.mp4&x-amz-CLIENTNETWORK=UNKNOWN&x-amz-CLOUDTYPEIN=CORP&x-amz-CLIENTTYPEIN=UNKNOWN&Signature=/nJLhyEJivvBkuxOJdnCRWWa4yE%3D&AWSAccessKeyId=0Lg7dAq3ZfHvePP8DKEU&Expires=1778499884&x-amz-limitrate=102400&response-content-type=video/mp4&x-amz-FSIZE=2183471772&x-amz-UID=10000004591358&x-amz-UFID=31374317010337932 |  |
| 多多 | 成功 |  | 2010.071 | 0.752 | 0.001 | 0.001 | 527.351 | 398.767 | 0.003 | 1082.63 | https://pan.baidu.com/s/1tCpt9UMVoL9OxQyvpKUYZA?pwd=yyds |  |
| 奕搜 | 成功 |  | 5831.872 | 0.823 | 0.002 | 0.001 | 3241.748 | 2342.315 | 0.001 | 246.275 | https://pan.quark.cn/s/e5345bdd71f6 |  |
| 如意资源 | 成功 |  | 10030.167 | 0.263 | 0.0 | 0.006 | 5689.717 | 2003.98 | 0.004 | 2335.54 | https://svip.ryiplay18.com/20260508/6294_cfc8934f/index.m3u8 |  |
| 布布影视 | 成功 |  | 7222.321 | 0.374 | 0.0 | 0.001 | 2376.701 | 2083.638 | 2445.418 | 315.606 | https://c167-obsdaz-ykj-01.obs.dualstack.cidc-rp-2006.joint.cmecloud.cn/1810c8ff2a78456b9348fadfe7ab0fd0086?response-content-disposition=attachment%3B%20filename%2A%3DUTF-8%27%274K.mp4&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20260511T091040Z&X-Amz-SignedHeaders=host&X-Amz-Expires=86400&X-Amz-Credential=AH4RWOMWLEL7ROYSF2S5%2F20260511%2Fcidc-rp-2006%2Fs3%2Faws4_request&t=2&u=1261698636582652615&ot=family&oi=1263000283947275586&f=FibTFWRt8ncqZsYDWQP5LF5BI3oB5_LXK&ext=eyJ1dCI6MX0%3D&X-Amz-Signature=e6411f7091b621576bb8d7d909861b24af7ccc31534058ba5f922f9b3e3970f0 |  |
| 微观短剧 | 成功 |  | 1003.93 | 0.216 | 0.013 | 248.101 | 277.61 | 319.032 | 0.003 | 158.316 | https://tv-video.cdn.drama.9ddm.com/22/A0/22A0BFFF46651CC23355B115F6307653.mp4?timestamp=1778491125&sign=fec954e79674337b237ea23f7b28c8b0 |  |
| 新韩剧网 | 成功 |  | 7755.181 | 0.66 | 0.001 | 0.001 | 1787.099 | 1795.046 | 1726.395 | 2444.93 | https://cdn.yzzyvip-29.com/20260201/16425_49d7d186/index.m3u8 |  |
| 星星短剧 | 成功 |  | 1312.555 | 0.285 | 0.0 | 0.001 | 474.826 | 667.716 | 0.002 | 169.047 | https://img.novel.wsljf.xyz/shortPlay-mp4/420424102051841/EvnIm1746774634078/abc6208e-390b-4533-a1a4-b9e5741cc384/540x960/output.m3u8 |  |
| 木偶 | 成功 |  | 4809.254 | 0.739 | 0.002 | 0.001 | 2603.497 | 1958.655 | 0.006 | 245.745 | https://115cdn.com/s/swf0zna36dh?password=p696 |  |
| 樱花动漫 | 失败 | 地址校验 | 17921.56 | 0.824 | 0.002 | 0.001 | 5591.636 | 4483.887 | 4378.839 | 3465.534 | https://vip.ffzy-plays.com/20260406/52101_7f60a1f1/index.m3u8 | HTTP 403 |
| 橘子TV | 成功 |  | 23600.01 | 0.907 | 4733.797 | 2369.152 | 2714.695 | 3152.487 | 10482.288 | 145.485 | https://tt0923.abc7722.com/m3u87/share/7256561/7452333/20260503/185008/1080/index.m3u8?sign=d3d54da921c54517e05e77dbe2fa959f&t=1778491146 |  |
| 欧歌 | 成功 |  | 8684.693 | 0.269 | 0.0 | 0.001 | 1850.67 | 1879.097 | 0.008 | 4953.747 | https://pan.baidu.com/s/1plecwmM4KBFNk_hU52nJIQ?pwd=8888 |  |
| 毒舌影视 | 成功 |  | 12746.636 | 0.833 | 0.001 | 3119.554 | 2856.473 | 2312.57 | 2320.877 | 2135.648 | https://v.gsuus.com/play/bYEWAopb/index.m3u8 |  |
| 河马短剧 | 成功 |  | 2699.909 | 0.975 | 0.002 | 872.067 | 462.605 | 1222.399 | 0.025 | 140.859 | https://dzzt-video.cbread.cn/620fddcdecb4360a618e381ed2e5f87d/6a02ec10/58/5x3/53x4/534x6/53468100014/612428785_1/612428785.720p.narrowv3.mp4 |  |
| 滴答影视 | 成功 |  | 4137.303 | 0.299 | 0.001 | 0.001 | 2073.148 | 1829.153 | 0.004 | 234.065 | https://pan.quark.cn/s/98a640e2e3ee |  |
| 潮流APP | 成功 |  | 799.817 | 0.225 | 0.002 | 127.017 | 119.685 | 183.088 | 275.842 | 93.507 | http://43.248.100.143:9090/nby/m3u8/getM3u8?name=jx.91by.top&time=1778491131979&url=NBY-e84585334a25c5b49078dfac81549a0b.m3u8 |  |
| 爱奇艺 | 成功 |  | 5891.657 | 0.499 | 0.016 | 3591.887 | 772.951 | 248.21 | 0.001 | 1277.417 | http://www.iqiyi.com/v_vd55wo89uk.html |  |
| 爱看 | 失败 | 地址校验 | 8824.56 | 0.241 | 0.0 | 0.001 | 1758.369 | 3781.176 | 0.003 | 3284.268 | https://vv.jisuzyv.com/play/epY8RMra/index.m3u8 | HTTPSConnectionPool(host='vv.jisuzyv.com', port=443): Max retries exceeded with url: /play/epY8RMra/index.m3u8 (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)'))) |
| 独播库 | 成功 |  | 8360.761 | 0.453 | 0.001 | 0.001 | 2255.204 | 1850.407 | 1959.834 | 2294.191 | https://vid.dbokutv.com/20260416/ppotb62-S71lT2yliZApDBSvkYzBsrmD3fpCJ4nBsHgTcyo5xOy6ejP7DiStHqR2qmCIqmCp8nE44oGZakRN0q/chunklist.m3u8 |  |
| 玩偶哥哥 | 成功 |  | 5542.325 | 0.27 | 0.0 | 0.0 | 1784.129 | 2740.62 | 0.004 | 1016.911 | https://pan.baidu.com/s/1hbYaibe8p-HfdhIUP7vvFA?pwd=f8x5 |  |
| 玩偶聚合 | 成功 |  | 5152.786 | 0.469 | 0.001 | 0.071 | 1981.493 | 1837.356 | 0.004 | 1332.684 | https://pan.baidu.com/s/1wlGptZsrXaSU5zwTNON1MA?pwd=wogg |  |
| 瓜子 | 成功 |  | 7940.109 | 0.869 | 0.004 | 0.057 | 2052.839 | 3816.879 | 1873.077 | 195.254 | https://vd.hxcztech.com/e5c3064aec3d555f7cda8bd651063a57/20260511171900/decry/vd/20260311/MjYwZjE1YTRkO/172631/1998_1080/aac/h264/hls/decrypt/index.m3u8 |  |
| 百度短剧 | 成功 |  | 1706.308 | 0.225 | 0.0 | 414.766 | 267.782 | 629.743 | 317.557 | 75.659 | http://vd3.bdstatic.com/mda-rh54j6is12ydd0q3/1080p/mv_cae264_backtrack_1080p_normal/1754453773225130912/mda-rh54j6is12ydd0q3.mp4?v_from_s=haokan-ui-video-hnb |  |
| 盘Ta | 成功 |  | 1097.991 | 0.366 | 0.0 | 348.93 | 285.777 | 283.783 | 0.062 | 176.93 | https://yun.139.com/shareweb/#/w/i/2sUfBKpu5QBqz |  |
| 盘尊社区 | 失败 | 视频详情 | 5531.835 | 0.288 | 0.0 | 0.001 | 3099.19 | 2431.121 | 0.0 | 0.0 |  | 详情缺少播放源或播放列表 |
| 盘聚 | 成功 |  | 6706.301 | 0.282 | 0.0 | 0.0 | 1718.697 | 2128.43 | 1800.951 | 1057.389 | https://pan.baidu.com/s/1NiQJW0DJBw8FR_Y1_k8Yig?pwd=ojmk |  |
| 短剧优选 | 成功 |  | 5656.843 | 0.7 | 667.969 | 3495.396 | 761.873 | 644.692 | 0.002 | 85.561 | https://cdn-vod-playlet.wtzw.com/asset/b936eac78f199fd865afbe3c5b707e7f/play_multi_video/6f7310c287644b7c813ab8e2eb7a4a0c/f1223068052dd7f1bc88718af4b2c0e4.m3u8 |  |
| 短剧网 | 成功 |  | 4417.637 | 0.273 | 0.001 | 0.0 | 2268.874 | 1916.611 | 0.008 | 231.127 | https://pan.quark.cn/s/5be7fea2409f |  |
| 糯米 | 成功 |  | 2168.295 | 0.736 | 0.002 | 485.383 | 633.856 | 164.456 | 423.097 | 459.878 | https://vip.123pan.cn/1853039965/dy/东北往事极恶不赦.m3u8 |  |
| 红果短剧 | 失败 | 分类列表 | 323.983 | 0.272 | 0.0 | 0.0 | 323.564 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| 网易云音乐 | 失败 | 未预期异常 | 1024.58 | 0.235 | 0.0 | 451.372 | 378.387 | 0.006 | 191.911 | 0.0 |  | Expecting value: line 1 column 1 (char 0) |
| 耐视点播 | 失败 | 分类列表 | 4142.567 | 0.377 | 0.0 | 0.0 | 4141.941 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| 腾讯视频 | 成功 |  | 1442.927 | 1.105 | 0.001 | 129.854 | 356.402 | 709.368 | 0.003 | 245.138 | https://v.qq.com/x/cover/mzc002009g0nh88/w4102d4f4ur.html |  |
| 至臻 | 成功 |  | 5894.17 | 0.267 | 0.0 | 0.001 | 2934.103 | 2716.617 | 0.005 | 242.594 | https://pan.quark.cn/s/b3e194803b59 |  |
| 芒果 | 成功 |  | 1278.354 | 0.402 | 0.001 | 0.001 | 358.011 | 799.218 | 0.002 | 119.857 | https://www.mgtv.com/b/731684/24256393.html |  |
| 茶杯狐 | 失败 | 地址校验 | 19055.053 | 0.504 | 0.001 | 2529.58 | 2371.592 | 2147.688 | 7660.056 | 4344.513 | https://vip.ffzy-plays.com/20260511/53449_d36f905d/index.m3u8 | HTTP 403 |
| 虎斑 | 成功 |  | 6133.107 | 0.696 | 0.002 | 0.003 | 2381.65 | 2642.406 | 0.016 | 1107.471 | https://pan.baidu.com/s/1aTT5yy3QuYPxWz-s4vz4aA?pwd=b5b5 |  |
| 蜡笔 | 失败 | 分类列表 | 14088.387 | 0.437 | 0.001 | 0.001 | 14087.493 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| 袋鼠影视 | 失败 | 地址校验 | 10935.384 | 0.385 | 0.001 | 0.001 | 2342.868 | 3275.719 | 2834.527 | 2481.177 | https://v10.baofeng10.com/video/xiangxinwojiaxianzhizhenmianmu/5d222521d913/index.m3u8 | HTTP 404 |
| 路漫漫 | 成功 |  | 11782.881 | 0.696 | 0.002 | 0.002 | 2280.56 | 2233.123 | 7067.145 | 200.599 | https://groupvideo.photo.qq.com/1071_0bc354askaabemajexgxvfus53yeexxqcjka.f0.mp4?dis_k=6561e50b5135d4185e983b0525402ac7&dis_t=1778491152 |  |
| 酷我听书 | 失败 | 地址校验 | 4458.433 | 1.308 | 0.002 | 372.305 | 103.709 | 3734.806 | 151.107 | 93.736 | http://lv.sycdn.kuwo.cn/077a00e43e156ef44b23d02c0a56d54b/6a019f09/resource/30106/trackmedia/long/M500002ZiI9a1sctnS.mp3?bitrate$128&format$mp3&source$kwplayerhd_ar_4.3.0.8_tianbao_T1A_qirui.apk&type$convert_url_with_sign&user$&loginUid$ | HTTP 403 |
| 酷狗音乐 | 成功 |  | 2153.668 | 0.936 | 607.914 | 320.309 | 305.78 | 344.103 | 419.749 | 153.579 | http://fsdg360.tx.kugou.com/202605111719/861f67a33672f42719baaf7550fcee0f/v3/17c458d87afb08f57335cc0363d43020/yp/full/ap1013_us0_mic85f71c379c462618de1399950957c33_pi6101_mx390528387_qumultitrack_s58909218.mkv?ft=car_203559_10049&fts=b05bb02d44717442054bac7624ed9a29&ext=.mkv |  |
| 金牌 | 成功 |  | 2672.666 | 0.279 | 0.001 | 730.819 | 253.058 | 249.113 | 282.459 | 1156.374 | https://ppvod011.blbtgg.com/splitOut/20260318/1267932/V20260318194542050871267932/index.m3u8?auth_key=1778491142-abd0b517defe4be9b67e23339a0f25f4-0-d7e21daaa2acc05aa51f10ac6df905be |  |
| 闪电 | 成功 |  | 2462.701 | 0.297 | 0.001 | 0.0 | 1296.327 | 811.421 | 0.028 | 354.173 | https://drive.uc.cn/s/e145774bc14b4?public=1 |  |
| 雷鲸 | 失败 | 视频详情 | 6833.186 | 0.539 | 0.001 | 0.003 | 4867.604 | 1964.778 | 0.0 | 0.0 |  | 详情缺少播放源或播放列表 |
| 飞快TV | 成功 |  | 22554.815 | 0.324 | 0.001 | 0.0 | 7166.533 | 5533.841 | 7336.142 | 2517.378 | https://cdn.yzzyvip-29.com/20260511/23657_6c73721a/index.m3u8 |  |
| 高清猫 | 失败 | 分类列表 | 1924.024 | 0.294 | 0.0 | 0.003 | 1923.488 | 0.0 | 0.0 | 0.0 |  | 分类视频列表为空 |
| 魔方APP | 失败 | 首页分类 | 1802.73 | 0.338 | 0.001 | 1801.897 | 0.0 | 0.0 | 0.0 | 0.0 |  | 分类列表为空 |
| 麦田影院 | 失败 | 未预期异常 | 2283.85 | 0.434 | 0.009 | 0.001 | 2280.007 | 0.0 | 0.0 | 0.0 |  | ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| 黑猫APP | 失败 | 未预期异常 | 10006.067 | 0.308 | 0.001 | 10003.74 | 0.0 | 0.0 | 0.0 | 0.0 |  | HTTPConnectionPool(host='app1-0-0.87333.cc', port=80): Read timed out. (read timeout=10) |
