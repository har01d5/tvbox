# 爬虫校验报告

- 生成时间: 2026-05-11T17:28:35+08:00
- 并发线程数: 16
- 总耗时(ms): 83.144秒
- 总数: 80
- 成功: 52
- 失败: 28

## 阶段失败统计

| 阶段 | 数量 |
| --- | ---: |
| 模块加载 | 0 |
| 初始化 | 0 |
| 首页分类 | 1 |
| 分类列表 | 7 |
| 视频详情 | 2 |
| 播放地址 | 1 |
| 地址校验 | 10 |
| 未预期异常 | 7 |

## 明细结果

| 爬虫 | 状态 | 失败阶段 | 总耗时 | 模块加载 | 初始化 | 首页分类 | 分类列表 | 视频详情 | 播放地址 | 地址校验 | 返回地址 | 错误信息 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 4K指南 | 成功 |  | 6.246秒 | 18.564ms | 0.001ms | 0.001ms | 3.701秒 | 2.302秒 | 0.005ms | 223.461ms | https://pan.quark.cn/s/e0726c4989dc |  |
| AAZ音乐 | 失败 | 未预期异常 | 10.073秒 | 21.666ms | 0.001ms | 10.022秒 | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='www.aaz.cx', port=443): Read timed out. (read timeout=10) |
| Atvp | 失败 | 未预期异常 | 74.176ms | 72.174ms | 0.004ms | 0.0ms | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | Atvp source is empty |
| PPnix | 成功 |  | 6.818秒 | 67.091ms | 0.001ms | 0.001ms | 2.283秒 | 2.767秒 | 0.009ms | 1.698秒 | https://www.ppnix.com/info/m3u8/8138/1080P.m3u8 |  |
| QQ音乐 | 成功 |  | 2.017秒 | 18.774ms | 0.014ms | 0.003ms | 564.331ms | 457.371ms | 808.743ms | 125.2ms | https://isure.stream.qqmusic.qq.com/F0000040rOp00lZYHC.flac?guid=8dc8082e567ec51f92c02ad898b602d9&vkey=AFBCE994CB600EC4CE12EC219FA4F829B974D735A8C1F26E42F5BF0EAF65F852E8089F4E1C99B2A0CB4E2C2112EFB19BAD223A4494F0E256__v2b9aadcd&uin=1152921504846230218&fromtag=119114&redirect=1 |  |
| UVod | 失败 | 地址校验 | 11.489秒 | 71.441ms | 2.082秒 | 1.915秒 | 2.511秒 | 1.9秒 | 1.972秒 | 1.037秒 | https://file-endpoint33.oledsa.com/content/dy-ljwl-shd-20260509-01.mp4/index.m3u8?st=QUGHtJfE4nZf129UbZF7Zw&e=1778506126 | HTTPSConnectionPool(host='file-endpoint33.oledsa.com', port=443): Max retries exceeded with url: /content/dy-ljwl-shd-20260509-01.mp4/index.m3u8?st=QUGHtJfE4nZf129UbZF7Zw&e=1778506126 (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)'))) |
| libvio | 失败 | 分类列表 | 1.99秒 | 19.695ms | 0.001ms | 0.003ms | 1.927秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| youknow | 成功 |  | 11.364秒 | 19.026ms | 0.001ms | 0.002ms | 3.51秒 | 2.55秒 | 2.61秒 | 2.633秒 | https://vip.dytt-tvs.com/20260504/18941_6de7c6c7/index.m3u8 |  |
| youtube | 失败 | 分类列表 | 1.481秒 | 17.753ms | 0.003ms | 0.024ms | 1.422秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 七味 | 成功 |  | 83.139秒 | 15.959ms | 0.001ms | 0.002ms | 2.71秒 | 2.329秒 | 76.779秒 | 1.274秒 | https://www.pcmp4.com/py/94740-3-1.html |  |
| 不太灵 | 失败 | 播放地址 | 6.747秒 | 18.413ms | 0.001ms | 2.158秒 | 2.513秒 | 2.028秒 | 0.005ms | 0.0ms |  | playerContent 未返回播放地址 |
| 世纪音乐 | 失败 | 未预期异常 | 10.057秒 | 14.727ms | 0.001ms | 10.028秒 | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='www.4c44.com', port=443): Max retries exceeded with url: / (Caused by ConnectTimeoutError(<HTTPSConnection(host='www.4c44.com', port=443) at 0x765ca062c190>, 'Connection to www.4c44.com timed out. (connect timeout=10)')) |
| 两个BT | 成功 |  | 9.337秒 | 22.04ms | 0.001ms | 0.001ms | 1.042秒 | 2.128秒 | 3.838秒 | 2.268秒 | https://zijieapi.douyinbyte.com/m3u8/dd0ca2ca11fcbf34e0a0d769ad4f7180.m3u8 |  |
| 乌云影视 | 成功 |  | 13.595秒 | 16.746ms | 0.001ms | 3.934秒 | 1.391秒 | 4.68秒 | 0.029ms | 3.545秒 | https://d1jdnmkc1n5cn4.cloudfront.net/gen_overseas/https://s2.bfllvip.com/video/yanxiaxing/a6ef854c0c1f/index.m3u8 |  |
| 乐兔 | 失败 | 未预期异常 | 10.086秒 | 15.354ms | 0.001ms | 0.002ms | 10.029秒 | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='www.letu.me', port=443): Read timed out. (read timeout=10) |
| 二小 | 成功 |  | 5.367秒 | 17.468ms | 0.001ms | 0.001ms | 3.284秒 | 1.81秒 | 0.006ms | 214.503ms | https://pan.quark.cn/s/b3e194803b59 |  |
| 人人电影 | 失败 | 分类列表 | 2.035秒 | 0.19ms | 0.0ms | 0.0ms | 2.035秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 人人视频 | 失败 | 地址校验 | 1.364秒 | 0.274ms | 0.0ms | 200.694ms | 303.574ms | 254.456ms | 414.43ms | 189.768ms | https://a3fkpcuk2gkkpmr.302.fledgecloud.com:56782/zj-302-cdn.bwcgee.cn/60b815c142c671f1ac975017e1f90402/30ffc804ae454cdaa23c4518d492908d-0e6b5348788a46aeb1399e154ae316e5-ld.mp4?auth_key=1778506118-f3dbd12de2de134c307286146528e67b-0-77c0e2bd54e3962136a573609528d961&clientType=web_pc&clientVersion=1.0.0&parseUsage=PLAY&uid=0&rk=64e5e240796347b1988a815b07a30f55&hevc=false&seasonId=57181 | HTTP 403 |
| 优酷 | 成功 |  | 1.181秒 | 0.42ms | 0.001ms | 0.001ms | 315.758ms | 595.309ms | 0.002ms | 268.692ms | https://v.youku.com/v_show/id_XNjUxODQ1MzE1Ng==.html |  |
| 低端影视 | 成功 |  | 5.464秒 | 0.32ms | 0.001ms | 0.001ms | 2.436秒 | 2.867秒 | 0.009ms | 159.907ms | https://hn.bfvvs.com/play/eXDLzQVe/index.m3u8 |  |
| 修罗 | 失败 | 地址校验 | 9.878秒 | 0.337ms | 0.0ms | 0.001ms | 3.278秒 | 723.329ms | 3.452秒 | 2.424秒 | https://v.xlys.ltd.ua/obj/0D97472BA572BE0FCC62FC525603718440A70C4AA52AE70704BB535D7DF74533 | HTTP 403 |
| 凡客TV | 成功 |  | 12.21秒 | 0.375ms | 0.001ms | 0.001ms | 1.512秒 | 2.522秒 | 3.957秒 | 4.218秒 | https://fktv.me/ysapi/m3u8/p/59a97924eaa4a4151f13a9dd67ce4eb5.m3u8 |  |
| 剧圈圈 | 成功 |  | 15.623秒 | 0.293ms | 0.001ms | 0.0ms | 3.392秒 | 2.414秒 | 7.265秒 | 2.552秒 | https://www.jqqzx.cc/play/62945-3-1.html |  |
| 剧迷 | 失败 | 地址校验 | 10.602秒 | 0.304ms | 0.0ms | 0.0ms | 4.154秒 | 2.106秒 | 2.456秒 | 1.886秒 | https://vip.dytt-see.com/20260505/36518_39a596c5/index.m3u8 | HTTP 403 |
| 博看听书 | 成功 |  | 4.324秒 | 0.264ms | 0.0ms | 3.164秒 | 274.713ms | 811.164ms | 0.002ms | 74.159ms | http://audio.bookan.com.cn/video1/audio/20200706001/aache64_133068a2.m4a |  |
| 厂长资源 | 失败 | 分类列表 | 7.248秒 | 0.339ms | 0.045ms | 0.001ms | 7.248秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 双星 | 成功 |  | 998.981ms | 0.259ms | 395.734ms | 0.005ms | 184.381ms | 180.82ms | 0.002ms | 237.224ms | https://pan.quark.cn/s/aefc43744bd3 |  |
| 听书 | 成功 |  | 17.868秒 | 0.298ms | 79.226ms | 0.001ms | 10.036秒 | 7.095秒 | 501.994ms | 155.769ms | http://audiopay.cos.tx.xmcdn.com/download/1.0.0/storages/b817-audiopay/16/AA/GKwRIaIGGaRGADgE-gEx_hMS-aacv2-48K.m4a?sign=b3b58e791e7df903ae4611a3eccea494&buy_key=FM&token=1791&timestamp=1778491740&duration=453 |  |
| 听友FM | 成功 |  | 27.006秒 | 1.075ms | 0.001ms | 6.99秒 | 7.159秒 | 10.25秒 | 2.424秒 | 182.124ms | https://file.hgeuz.cn/stream/eJwANwDI_wJVZgVKIIrU0ECux-GJ1PSt38ahythCqsH-r9TAQ4rj5F94rOjbQKjk063xyIX2z3hfeGcIHF4BAAD__5DtISY.?ts=1778488205&sign=625c3a14e1a6c8df8d4d35663d542452 |  |
| 四万影视 | 失败 | 未预期异常 | 818.122ms | 0.267ms | 0.0ms | 0.0ms | 816.221ms | 0.0ms | 0.0ms | 0.0ms |  | HTTPSConnectionPool(host='40000.me', port=443): Max retries exceeded with url: /api/maccms?ac=detail&t=20&pg=1&by=time (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1081)'))) |
| 在线之家 | 成功 |  | 7.721秒 | 0.3ms | 0.0ms | 0.001ms | 2.071秒 | 2.984秒 | 2.361秒 | 304.078ms | https://media-sxty-fy-corp.sx3oss.ctyunxs.cn/CORPCLOUD/f076ccf5-a095-45a2-b086-cbf66f4aa40d.mp4?response-content-disposition=attachment%3Bfilename%3D%22%E9%93%81%E8%A1%80%E6%88%98%E5%A3%AB%E6%9D%80%E6%88%AE%E4%B9%8B%E5%9C%B02025HD1080P.mp4%22%3Bfilename*%3DUTF-8%27%27%25E9%2593%2581%25E8%25A1%2580%25E6%2588%2598%25E5%25A3%25AB%25E6%259D%2580%25E6%2588%25AE%25E4%25B9%258B%25E5%259C%25B02025HD1080P.mp4&x-amz-CLIENTNETWORK=UNKNOWN&x-amz-CLOUDTYPEIN=CORP&x-amz-CLIENTTYPEIN=UNKNOWN&Signature=/nJLhyEJivvBkuxOJdnCRWWa4yE%3D&AWSAccessKeyId=0Lg7dAq3ZfHvePP8DKEU&Expires=1778499884&x-amz-limitrate=102400&response-content-type=video/mp4&x-amz-FSIZE=2183471772&x-amz-UID=10000004591358&x-amz-UFID=31374317010337932 |  |
| 多多 | 成功 |  | 2.105秒 | 0.228ms | 0.0ms | 0.0ms | 601.933ms | 424.128ms | 0.003ms | 1.078秒 | https://pan.baidu.com/s/1tCpt9UMVoL9OxQyvpKUYZA?pwd=yyds |  |
| 奕搜 | 成功 |  | 4.636秒 | 0.219ms | 0.0ms | 0.0ms | 2.955秒 | 1.448秒 | 0.001ms | 233.257ms | https://pan.quark.cn/s/e5345bdd71f6 |  |
| 如意资源 | 成功 |  | 9.097秒 | 0.222ms | 0.0ms | 0.005ms | 4.492秒 | 2.026秒 | 0.004ms | 2.578秒 | https://svip.ryiplay18.com/20260508/6294_cfc8934f/index.m3u8 |  |
| 布布影视 | 成功 |  | 6.497秒 | 0.404ms | 0.0ms | 0.0ms | 2.43秒 | 1.125秒 | 2.567秒 | 374.332ms | https://c167-obsdaz-ykj-01.obs.dualstack.cidc-rp-2006.joint.cmecloud.cn/1810c8ff2a78456b9348fadfe7ab0fd0086?response-content-disposition=attachment%3B%20filename%2A%3DUTF-8%27%274K.mp4&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20260511T092851Z&X-Amz-SignedHeaders=host&X-Amz-Expires=86400&X-Amz-Credential=AH4RWOMWLEL7ROYSF2S5%2F20260511%2Fcidc-rp-2006%2Fs3%2Faws4_request&t=2&u=1261698636582652615&ot=family&oi=1263000283947275586&f=FibTFWRt8ncqZsYDWQP5LF5BI3oB5_LXK&ext=eyJ1dCI6MX0%3D&X-Amz-Signature=383b6995c3878baa714cf17930c946afa190baaeee6ebdb124848486c673df5d |  |
| 微观短剧 | 成功 |  | 1.119秒 | 0.437ms | 0.024ms | 215.819ms | 287.36ms | 414.49ms | 0.002ms | 200.074ms | https://tv-video.cdn.drama.9ddm.com/22/A0/22A0BFFF46651CC23355B115F6307653.mp4?timestamp=1778491728&sign=21f81503258a96116204438bffb60b64 |  |
| 新韩剧网 | 成功 |  | 5.801秒 | 0.849ms | 0.002ms | 0.001ms | 801.355ms | 763.183ms | 1.701秒 | 2.534秒 | https://cdn.yzzyvip-29.com/20260201/16425_49d7d186/index.m3u8 |  |
| 星星短剧 | 成功 |  | 1.193秒 | 0.255ms | 0.001ms | 0.001ms | 404.959ms | 637.839ms | 0.002ms | 149.49ms | https://img.novel.wsljf.xyz/shortPlay-mp4/420424102051841/EvnIm1746774634078/abc6208e-390b-4533-a1a4-b9e5741cc384/540x960/output.m3u8 |  |
| 木偶 | 成功 |  | 3.528秒 | 0.27ms | 0.0ms | 0.0ms | 2.301秒 | 973.582ms | 0.008ms | 252.448ms | https://115cdn.com/s/swf0zna36dh?password=p696 |  |
| 樱花动漫 | 失败 | 地址校验 | 15.623秒 | 0.307ms | 0.001ms | 0.0ms | 2.436秒 | 4.125秒 | 4.667秒 | 4.394秒 | https://vip.ffzy-plays.com/20260406/52101_7f60a1f1/index.m3u8 | HTTP 403 |
| 橘子TV | 成功 |  | 19.566秒 | 0.752ms | 5.499秒 | 1.524秒 | 1.774秒 | 4.101秒 | 6.477秒 | 189.92ms | https://tt0923.abc7722.com/m3u87/share/7256561/7452333/20260503/185008/1080/index.m3u8?sign=aaaa59b28850a3740b30d52ac1e97ece&t=1778491746 |  |
| 欧歌 | 成功 |  | 4.91秒 | 0.309ms | 0.0ms | 0.0ms | 1.92秒 | 1.843秒 | 0.005ms | 1.147秒 | https://pan.baidu.com/s/1plecwmM4KBFNk_hU52nJIQ?pwd=8888 |  |
| 毒舌影视 | 成功 |  | 9.0秒 | 0.626ms | 0.001ms | 2.654秒 | 2.053秒 | 1.064秒 | 2.127秒 | 1.101秒 | https://v.gsuus.com/play/bYEWAopb/index.m3u8 |  |
| 河马短剧 | 成功 |  | 2.648秒 | 0.317ms | 0.0ms | 709.229ms | 694.868ms | 1.125秒 | 0.029ms | 117.451ms | https://dzzt-video.cbread.cn/a47e0c4b6634c6ba52175dc0da481b91/6a02de00/58/5x3/53x4/534x6/53468100014/612428785_1/612428785.720p.narrowv3.mp4 |  |
| 滴答影视 | 成功 |  | 3.199秒 | 0.346ms | 0.0ms | 0.001ms | 946.511ms | 2.031秒 | 0.007ms | 220.25ms | https://pan.quark.cn/s/98a640e2e3ee |  |
| 潮流APP | 成功 |  | 742.05ms | 0.333ms | 0.002ms | 107.311ms | 110.098ms | 151.707ms | 273.766ms | 98.458ms | http://43.248.100.143:9090/nby/m3u8/getM3u8?name=jx.91by.top&time=1778491732324&url=NBY-e84585334a25c5b49078dfac81549a0b.m3u8 |  |
| 爱奇艺 | 成功 |  | 4.643秒 | 0.636ms | 0.018ms | 3.394秒 | 874.268ms | 182.477ms | 0.002ms | 190.347ms | http://www.iqiyi.com/v_vd55wo89uk.html |  |
| 爱看 | 失败 | 地址校验 | 6.657秒 | 0.269ms | 0.0ms | 0.001ms | 728.826ms | 4.027秒 | 0.002ms | 1.901秒 | https://vv.jisuzyv.com/play/epY8RMra/index.m3u8 | HTTPSConnectionPool(host='vv.jisuzyv.com', port=443): Max retries exceeded with url: /play/epY8RMra/index.m3u8 (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1081)'))) |
| 独播库 | 成功 |  | 6.246秒 | 0.326ms | 0.001ms | 0.001ms | 1.765秒 | 819.929ms | 1.841秒 | 1.819秒 | https://vid.dbokutv.com/20260416/ppotb62-S71lT2yliZApDBSvkYzBsrmD3fpCJ4nBsHgTcyo5xOy6ejP7DiStHqR2qmCIqmCp8nE44oGZakRN0q/chunklist.m3u8 |  |
| 玩偶哥哥 | 成功 |  | 4.148秒 | 0.306ms | 0.0ms | 0.0ms | 1.972秒 | 1.08秒 | 0.004ms | 1.095秒 | https://pan.baidu.com/s/1hbYaibe8p-HfdhIUP7vvFA?pwd=f8x5 |  |
| 玩偶聚合 | 成功 |  | 14.959秒 | 0.423ms | 0.0ms | 0.05ms | 11.972秒 | 1.814秒 | 0.002ms | 1.172秒 | https://pan.baidu.com/s/1wlGptZsrXaSU5zwTNON1MA?pwd=wogg |  |
| 瓜子 | 成功 |  | 8.262秒 | 0.282ms | 0.001ms | 0.016ms | 2.316秒 | 3.871秒 | 1.933秒 | 140.392ms | https://vd.hxcztech.com/559b97ac0b0f74c60345b7ffa578cbe1/20260511172901/decry/vd/20260311/MjYwZjE1YTRkO/172631/1998_1080/aac/h264/hls/decrypt/index.m3u8 |  |
| 百度短剧 | 成功 |  | 1.543秒 | 0.365ms | 0.001ms | 353.154ms | 261.247ms | 585.185ms | 250.435ms | 91.864ms | http://vd3.bdstatic.com/mda-rh54j6is12ydd0q3/1080p/mv_cae264_backtrack_1080p_normal/1754453773225130912/mda-rh54j6is12ydd0q3.mp4?v_from_s=haokan-ui-video-hna |  |
| 盘Ta | 成功 |  | 1.793秒 | 0.402ms | 0.001ms | 309.056ms | 276.866ms | 1.046秒 | 0.021ms | 159.473ms | https://yun.139.com/shareweb/#/w/i/2sUfBKpu5QBqz |  |
| 盘尊社区 | 失败 | 视频详情 | 5.066秒 | 0.613ms | 0.008ms | 0.001ms | 2.645秒 | 2.419秒 | 0.0ms | 0.0ms |  | 详情缺少播放源或播放列表 |
| 盘聚 | 成功 |  | 6.844秒 | 0.333ms | 0.0ms | 0.0ms | 1.758秒 | 1.816秒 | 1.861秒 | 1.407秒 | https://pan.baidu.com/s/1NiQJW0DJBw8FR_Y1_k8Yig?pwd=ojmk |  |
| 短剧优选 | 成功 |  | 5.062秒 | 2.781ms | 574.02ms | 3.582秒 | 457.51ms | 359.758ms | 0.002ms | 84.042ms | https://cdn-vod-playlet.wtzw.com/asset/b936eac78f199fd865afbe3c5b707e7f/play_multi_video/6f7310c287644b7c813ab8e2eb7a4a0c/f1223068052dd7f1bc88718af4b2c0e4.m3u8 |  |
| 短剧网 | 成功 |  | 5.298秒 | 0.443ms | 0.001ms | 0.001ms | 1.609秒 | 3.46秒 | 0.004ms | 227.385ms | https://pan.quark.cn/s/5be7fea2409f |  |
| 糯米 | 成功 |  | 2.007秒 | 0.531ms | 0.001ms | 315.393ms | 752.313ms | 213.447ms | 354.939ms | 369.513ms | https://vip.123pan.cn/1853039965/dy/东北往事极恶不赦.m3u8 |  |
| 红果短剧 | 失败 | 分类列表 | 216.094ms | 0.282ms | 0.0ms | 0.0ms | 215.661ms | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 网易云音乐 | 失败 | 未预期异常 | 1.207秒 | 0.246ms | 0.0ms | 489.171ms | 526.026ms | 0.005ms | 189.656ms | 0.0ms |  | Expecting value: line 1 column 1 (char 0) |
| 耐视点播 | 失败 | 分类列表 | 3.008秒 | 0.322ms | 0.0ms | 0.0ms | 3.007秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 腾讯视频 | 成功 |  | 1.451秒 | 0.726ms | 0.0ms | 160.171ms | 291.765ms | 720.683ms | 0.003ms | 276.597ms | https://v.qq.com/x/cover/mzc002009g0nh88/w4102d4f4ur.html |  |
| 至臻 | 成功 |  | 4.668秒 | 0.242ms | 0.0ms | 0.0ms | 2.585秒 | 1.849秒 | 0.005ms | 232.714ms | https://pan.quark.cn/s/b3e194803b59 |  |
| 芒果 | 成功 |  | 1.297秒 | 0.386ms | 0.001ms | 0.001ms | 352.577ms | 818.278ms | 0.004ms | 125.348ms | https://www.mgtv.com/b/731684/24256393.html |  |
| 茶杯狐 | 失败 | 地址校验 | 16.023秒 | 0.426ms | 0.0ms | 2.96秒 | 2.096秒 | 3.152秒 | 3.161秒 | 4.653秒 | https://vip.ffzy-plays.com/20260511/53449_d36f905d/index.m3u8 | HTTP 403 |
| 虎斑 | 成功 |  | 2.02秒 | 0.264ms | 0.001ms | 0.001ms | 373.379ms | 618.461ms | 0.009ms | 1.027秒 | https://pan.baidu.com/s/1aTT5yy3QuYPxWz-s4vz4aA?pwd=b5b5 |  |
| 蜡笔 | 成功 |  | 5.166秒 | 0.252ms | 0.001ms | 0.0ms | 2.231秒 | 1.814秒 | 0.008ms | 1.12秒 | https://pan.baidu.com/s/1NiPgbk9_FIhSYfmGm-Cqxg?pwd=q5m6 |  |
| 袋鼠影视 | 失败 | 地址校验 | 8.874秒 | 0.299ms | 0.0ms | 0.001ms | 2.325秒 | 1.956秒 | 2.4秒 | 2.192秒 | https://v10.baofeng10.com/video/xiangxinwojiaxianzhizhenmianmu/5d222521d913/index.m3u8 | HTTP 404 |
| 路漫漫 | 成功 |  | 8.519秒 | 0.32ms | 0.001ms | 0.001ms | 1.473秒 | 2.21秒 | 4.644秒 | 191.982ms | https://groupvideo.photo.qq.com/1071_0bc354askaabemajexgxvfus53yeexxqcjka.f0.mp4?dis_k=6561e50b5135d4185e983b0525402ac7&dis_t=1778491152 |  |
| 酷我听书 | 失败 | 地址校验 | 4.358秒 | 0.376ms | 0.001ms | 409.782ms | 117.264ms | 3.601秒 | 137.227ms | 90.455ms | http://lv.sycdn.kuwo.cn/a7d133039fac4e70e5176a27ae17b68f/6a01a161/resource/30106/trackmedia/long/M500002ZiI9a1sctnS.mp3?bitrate$128&format$mp3&source$kwplayerhd_ar_4.3.0.8_tianbao_T1A_qirui.apk&type$convert_url_with_sign&user$&loginUid$ | HTTP 403 |
| 酷狗音乐 | 成功 |  | 1.998秒 | 0.485ms | 537.932ms | 301.312ms | 271.127ms | 312.4ms | 383.732ms | 188.435ms | http://fsdg360.hw.kugou.com/202605111729/33da97badc60d8d2319c18f1d24f6f46/v3/17c458d87afb08f57335cc0363d43020/yp/full/ap1013_us0_mic85f71c379c462618de1399950957c33_pi6101_mx390528387_qumultitrack_s58909218.mkv?ft=car_203559_10049&fts=b05bb02d44717442054bac7624ed9a29&ext=.mkv |  |
| 金牌 | 成功 |  | 2.123秒 | 0.292ms | 0.001ms | 686.093ms | 236.707ms | 258.647ms | 247.036ms | 692.828ms | https://ppvod011.blbtgg.com/splitOut/20260318/1267932/V20260318194542050871267932/index.m3u8?auth_key=1778491743-3aa8bf488dd641afb71e477f4f6c5ff4-0-0dd672092040bccbac1b521eb21c9f6c |  |
| 闪电 | 成功 |  | 2.482秒 | 0.266ms | 0.0ms | 0.0ms | 1.206秒 | 902.988ms | 0.008ms | 372.191ms | https://drive.uc.cn/s/e145774bc14b4?public=1 |  |
| 雷鲸 | 失败 | 视频详情 | 5.172秒 | 0.585ms | 0.001ms | 0.002ms | 2.805秒 | 2.366秒 | 0.0ms | 0.0ms |  | 详情缺少播放源或播放列表 |
| 飞快TV | 成功 |  | 17.17秒 | 0.374ms | 0.001ms | 0.0ms | 4.56秒 | 5.097秒 | 6.227秒 | 1.285秒 | https://cdn.yzzyvip-29.com/20260511/23657_6c73721a/index.m3u8 |  |
| 高清猫 | 失败 | 分类列表 | 2.022秒 | 0.377ms | 0.0ms | 0.004ms | 2.021秒 | 0.0ms | 0.0ms | 0.0ms |  | 分类视频列表为空 |
| 魔方APP | 失败 | 首页分类 | 2.091秒 | 0.57ms | 0.001ms | 2.091秒 | 0.0ms | 0.0ms | 0.0ms | 0.0ms |  | 分类列表为空 |
| 麦田影院 | 失败 | 未预期异常 | 2.46秒 | 0.474ms | 0.001ms | 0.001ms | 2.458秒 | 0.0ms | 0.0ms | 0.0ms |  | ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| 黑猫APP | 失败 | 地址校验 | 8.611秒 | 0.46ms | 0.001ms | 1.371秒 | 913.696ms | 1.961秒 | 0.009ms | 4.364秒 | https://vip.ffzy-plays.com/20260511/53448_da254751/index.m3u8 | HTTP 403 |
